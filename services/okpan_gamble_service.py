import random

from models.okpan_game_result import OkpanGameResult
from models.okpan_wallet import OkpanWallet


class OkpanGambleService:
    """
    도박에 사용되는 옥판 차감 및 지급을 담당한다.

    유저는 옥판의 총개수만 알 수 있으며,
    실제 등급은 시스템 내부에서만 처리한다.
    """

    # 등급 추첨 가중치
    #
    # 1등급:   2 / 1000 = 0.2%
    # 2등급: 200 / 1000 = 20%
    # 3등급: 798 / 1000 = 79.8%
    GRADE_1_WEIGHT = 2
    GRADE_2_WEIGHT = 200
    TOTAL_WEIGHT = 1000

    # ============================================
    # 배팅 옥판 무작위 차감
    # ============================================

    async def deduct_random_okpan(
        self,
        conn,
        discord_id: str,
        amount: int
    ) -> None:
        """
        실제 보유 옥판 중 지정한 개수만큼 무작위로 차감한다.

        유저는 어떤 등급의 옥판이 차감됐는지 알 수 없다.

        이 메서드는 반드시 트랜잭션 중인 Connection으로 호출한다.
        """

        if amount <= 0:
            raise ValueError(
                "배팅할 옥판은 1개 이상이어야 합니다."
            )

        # 해당 유저 행을 잠근 상태로 현재 옥판 조회
        wallet = await self._get_wallet_for_update(
            conn,
            discord_id
        )

        total_okpan = wallet.get_total_okpan()

        if total_okpan < amount:
            raise RuntimeError(
                f"보유한 옥판이 부족합니다. "
                f"현재 보유 옥판: {total_okpan}개"
            )

        remaining_grade1 = wallet.grade1
        remaining_grade2 = wallet.grade2
        remaining_grade3 = wallet.grade3

        deducted_grade1 = 0
        deducted_grade2 = 0
        deducted_grade3 = 0

        """
        실제 보유 옥판 중 하나씩 무작위로 선택한다.

        예:
        1등급 1개
        2등급 3개
        3등급 6개

        총 10개의 옥판 중 하나를 같은 확률로 선택한다.
        """

        for _ in range(amount):

            remaining_total = (
                remaining_grade1
                + remaining_grade2
                + remaining_grade3
            )

            # Java nextLong(remainingTotal)과 동일하게
            # 0 이상 remaining_total 미만
            random_number = random.randrange(
                remaining_total
            )

            if random_number < remaining_grade1:

                remaining_grade1 -= 1
                deducted_grade1 += 1

            elif (
                random_number
                < remaining_grade1 + remaining_grade2
            ):

                remaining_grade2 -= 1
                deducted_grade2 += 1

            else:

                remaining_grade3 -= 1
                deducted_grade3 += 1

        sql = """
            UPDATE users
            SET okpan_grade_1 = okpan_grade_1 - %s,
                okpan_grade_2 = okpan_grade_2 - %s,
                okpan_grade_3 = okpan_grade_3 - %s
            WHERE discord_id = %s
        """

        cursor = await conn.cursor()

        try:
            await cursor.execute(
                sql,
                (
                    deducted_grade1,
                    deducted_grade2,
                    deducted_grade3,
                    discord_id
                )
            )

            if cursor.rowcount != 1:
                raise RuntimeError(
                    "배팅 옥판을 차감하지 못했습니다."
                )

        finally:
            await cursor.close()

    # ============================================
    # 도박 보상 옥판 지급
    # ============================================

    async def add_random_reward_okpan(
        self,
        conn,
        discord_id: str,
        amount: int
    ) -> OkpanGameResult:
        """
        도박 보상 옥판을 생성하고 DB에 지급한다.

        지급할 옥판마다 등급을 개별 추첨한다.
        """

        if amount < 0:
            raise ValueError(
                "지급할 옥판 개수는 0개 이상이어야 합니다."
            )

        if amount == 0:
            return OkpanGameResult(
                grade1=0,
                grade2=0,
                grade3=0
            )

        grade1 = 0
        grade2 = 0
        grade3 = 0

        for _ in range(amount):

            # 1 ~ 1000
            random_number = random.randint(
                1,
                self.TOTAL_WEIGHT
            )

            if random_number <= self.GRADE_1_WEIGHT:

                grade1 += 1

            elif (
                random_number
                <= self.GRADE_1_WEIGHT
                + self.GRADE_2_WEIGHT
            ):

                grade2 += 1

            else:

                grade3 += 1

        sql = """
            UPDATE users
            SET okpan_grade_1 = okpan_grade_1 + %s,
                okpan_grade_2 = okpan_grade_2 + %s,
                okpan_grade_3 = okpan_grade_3 + %s
            WHERE discord_id = %s
        """

        cursor = await conn.cursor()

        try:
            await cursor.execute(
                sql,
                (
                    grade1,
                    grade2,
                    grade3,
                    discord_id
                )
            )

            if cursor.rowcount != 1:
                raise RuntimeError(
                    "도박 보상 옥판을 지급하지 못했습니다."
                )

        finally:
            await cursor.close()

        return OkpanGameResult(
            grade1=grade1,
            grade2=grade2,
            grade3=grade3
        )

    # ============================================
    # 전체 옥판 개수 조회
    # ============================================

    async def get_total_okpan(
        self,
        conn,
        discord_id: str
    ) -> int:

        wallet = await self._get_wallet(
            conn,
            discord_id
        )

        return wallet.get_total_okpan()

    # ============================================
    # 잠금 상태로 지갑 조회
    # ============================================

    async def _get_wallet_for_update(
        self,
        conn,
        discord_id: str
    ) -> OkpanWallet:
        """
        트랜잭션 중 옥판이 동시에 변경되지 않도록
        해당 유저 행을 잠그고 지갑을 조회한다.
        """

        sql = """
            SELECT
                money,
                okpan_grade_1,
                okpan_grade_2,
                okpan_grade_3
            FROM users
            WHERE discord_id = %s
            FOR UPDATE
        """

        cursor = await conn.cursor(
            dictionary=True
        )

        try:
            await cursor.execute(
                sql,
                (discord_id,)
            )

            row = await cursor.fetchone()

            if row is not None:
                return self._create_wallet(
                    row
                )

        finally:
            await cursor.close()

        raise RuntimeError(
            "유저의 옥판 정보를 찾을 수 없습니다."
        )

    # ============================================
    # 일반 지갑 조회
    # ============================================

    async def _get_wallet(
        self,
        conn,
        discord_id: str
    ) -> OkpanWallet:

        sql = """
            SELECT
                money,
                okpan_grade_1,
                okpan_grade_2,
                okpan_grade_3
            FROM users
            WHERE discord_id = %s
        """

        cursor = await conn.cursor(
            dictionary=True
        )

        try:
            await cursor.execute(
                sql,
                (discord_id,)
            )

            row = await cursor.fetchone()

            if row is not None:
                return self._create_wallet(
                    row
                )

        finally:
            await cursor.close()

        raise RuntimeError(
            "유저의 옥판 정보를 찾을 수 없습니다."
        )

    # ============================================
    # Row → OkpanWallet 변환
    # ============================================

    def _create_wallet(
        self,
        row: dict
    ) -> OkpanWallet:

        return OkpanWallet(
            money=row["money"],
            grade1=row["okpan_grade_1"],
            grade2=row["okpan_grade_2"],
            grade3=row["okpan_grade_3"]
        )