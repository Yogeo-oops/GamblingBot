import random

from models.okpan_game_result import OkpanGameResult
from models.okpan_wallet import OkpanWallet


class OkpanGambleService:
    """
    도박에 사용되는 옥판 차감 및 지급을 담당한다.

    SQLite 기반으로 동작한다.

    유저는 옥판의 총개수만 알 수 있으며,
    실제 등급은 시스템 내부에서만 처리한다.
    """

    # ============================================
    # 등급 추첨 가중치
    # ============================================
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
        실제 보유 옥판 중 지정한 개수만큼
        무작위로 차감한다.

        유저는 어떤 등급의 옥판이 차감됐는지
        알 수 없다.

        이 메서드는 반드시
        트랜잭션 중인 Connection으로 호출한다.
        """

        if amount <= 0:

            raise ValueError(
                "배팅할 옥판은 1개 이상이어야 합니다."
            )

        # ========================================
        # 현재 지갑 조회
        # ========================================
        #
        # SQLite에서는 MySQL의 FOR UPDATE를
        # 사용할 수 없다.
        #
        # 호출하는 서비스에서 BEGIN IMMEDIATE를
        # 사용하여 쓰기 트랜잭션을 잠근다.

        wallet = await self._get_wallet(
            conn,
            discord_id
        )

        total_okpan = (
            wallet.get_total_okpan()
        )

        if total_okpan < amount:

            raise RuntimeError(
                "보유한 옥판이 부족합니다. "
                f"현재 보유 옥판: "
                f"{total_okpan:,}개"
            )

        # ========================================
        # 현재 등급별 옥판 수
        # ========================================

        remaining_grade1 = (
            wallet.grade1
        )

        remaining_grade2 = (
            wallet.grade2
        )

        remaining_grade3 = (
            wallet.grade3
        )

        deducted_grade1 = 0
        deducted_grade2 = 0
        deducted_grade3 = 0

        # ========================================
        # 실제 보유 옥판 중 무작위 차감
        # ========================================

        for _ in range(amount):

            remaining_total = (
                remaining_grade1
                + remaining_grade2
                + remaining_grade3
            )

            random_number = (
                random.randrange(
                    remaining_total
                )
            )

            if (
                random_number
                < remaining_grade1
            ):

                remaining_grade1 -= 1
                deducted_grade1 += 1

            elif (
                random_number
                < remaining_grade1
                + remaining_grade2
            ):

                remaining_grade2 -= 1
                deducted_grade2 += 1

            else:

                remaining_grade3 -= 1
                deducted_grade3 += 1

        # ========================================
        # DB 반영
        # ========================================

        cursor = await conn.execute(
            """
            UPDATE users
            SET okpan_grade_1 = okpan_grade_1 - ?,
                okpan_grade_2 = okpan_grade_2 - ?,
                okpan_grade_3 = okpan_grade_3 - ?
            WHERE discord_id = ?
            """,
            (
                deducted_grade1,
                deducted_grade2,
                deducted_grade3,
                discord_id
            )
        )

        if cursor.rowcount != 1:

            await cursor.close()

            raise RuntimeError(
                "배팅 옥판을 차감하지 못했습니다."
            )

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
        도박 보상 옥판을 생성하여 지급한다.

        지급되는 옥판은 한 개마다
        내부 등급을 개별 추첨한다.
        """

        if amount < 0:

            raise ValueError(
                "지급할 옥판 개수는 "
                "0개 이상이어야 합니다."
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

        # ========================================
        # 지급 옥판 등급 추첨
        # ========================================

        for _ in range(amount):

            random_number = (
                random.randint(
                    1,
                    self.TOTAL_WEIGHT
                )
            )

            if (
                random_number
                <= self.GRADE_1_WEIGHT
            ):

                grade1 += 1

            elif (
                random_number
                <= (
                    self.GRADE_1_WEIGHT
                    + self.GRADE_2_WEIGHT
                )
            ):

                grade2 += 1

            else:

                grade3 += 1

        # ========================================
        # DB 지급
        # ========================================

        cursor = await conn.execute(
            """
            UPDATE users
            SET okpan_grade_1 = okpan_grade_1 + ?,
                okpan_grade_2 = okpan_grade_2 + ?,
                okpan_grade_3 = okpan_grade_3 + ?
            WHERE discord_id = ?
            """,
            (
                grade1,
                grade2,
                grade3,
                discord_id
            )
        )

        if cursor.rowcount != 1:

            await cursor.close()

            raise RuntimeError(
                "도박 보상 옥판을 지급하지 못했습니다."
            )

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

        return (
            wallet.get_total_okpan()
        )

    # ============================================
    # 지갑 조회
    # ============================================

    async def _get_wallet(
        self,
        conn,
        discord_id: str
    ) -> OkpanWallet:

        cursor = await conn.execute(
            """
            SELECT
                money,
                okpan_grade_1,
                okpan_grade_2,
                okpan_grade_3
            FROM users
            WHERE discord_id = ?
            """,
            (
                discord_id,
            )
        )

        row = await cursor.fetchone()

        await cursor.close()

        if row is None:

            raise RuntimeError(
                "유저의 옥판 정보를 찾을 수 없습니다."
            )

        return OkpanWallet(
            money=int(
                row["money"]
            ),
            grade1=int(
                row["okpan_grade_1"]
            ),
            grade2=int(
                row["okpan_grade_2"]
            ),
            grade3=int(
                row["okpan_grade_3"]
            )
        )