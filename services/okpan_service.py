import random

from database import Database
from models.okpan_exchange_result import OkpanExchangeResult
from models.okpan_wallet import OkpanWallet


class OkpanService:
    """
    옥판 구매, 무작위 환전, 운영진 지급 및 조회를 담당한다.
    """

    # 돈으로 옥판 구매
    # 100문 = 옥판 1개
    OKPAN_PURCHASE_PRICE = 100

    # 옥판 등급별 환전 가치
    GRADE_1_VALUE = 2000
    GRADE_2_VALUE = 100
    GRADE_3_VALUE = 20

    # ============================================
    # 지갑 생성 / 조회
    # ============================================

    async def get_or_create_wallet(
        self,
        discord_id: str,
        username: str
    ) -> OkpanWallet:

        conn = await Database.get_connection()

        try:
            await conn.start_transaction()

            await self._create_or_update_user(
                conn,
                discord_id,
                username
            )

            wallet = await self._get_wallet(
                conn,
                discord_id
            )

            await conn.commit()

            return wallet

        except Exception:
            await conn.rollback()
            raise

        finally:
            await conn.close()

    async def get_wallet(
        self,
        discord_id: str
    ) -> OkpanWallet:

        conn = await Database.get_connection()

        try:
            return await self._get_wallet(
                conn,
                discord_id
            )

        finally:
            await conn.close()

    # ============================================
    # 옥판 구매
    # ============================================

    async def buy_okpan(
        self,
        discord_id: str,
        username: str,
        amount: int
    ) -> OkpanWallet:

        if amount <= 0:
            raise ValueError(
                "구매할 옥판은 1개 이상이어야 합니다."
            )

        cost = (
            amount
            * self.OKPAN_PURCHASE_PRICE
        )

        conn = await Database.get_connection()

        try:
            await conn.start_transaction()

            await self._create_or_update_user(
                conn,
                discord_id,
                username
            )

            sql = """
                UPDATE users
                SET money = money - %s,
                    okpan_grade_2 = okpan_grade_2 + %s
                WHERE discord_id = %s
                  AND money >= %s
            """

            cursor = await conn.cursor()

            try:
                await cursor.execute(
                    sql,
                    (
                        cost,
                        amount,
                        discord_id,
                        cost
                    )
                )

                if cursor.rowcount != 1:
                    raise RuntimeError(
                        "옥판을 구매하기 위한 돈이 부족합니다."
                    )

            finally:
                await cursor.close()

            wallet = await self._get_wallet(
                conn,
                discord_id
            )

            await conn.commit()

            return wallet

        except Exception:
            await conn.rollback()
            raise

        finally:
            await conn.close()

    # ============================================
    # 옥판 환전
    # ============================================

    async def exchange_random_okpan(
        self,
        discord_id: str,
        amount: int
    ) -> OkpanExchangeResult:

        if amount <= 0:
            raise ValueError(
                "환전할 옥판은 1개 이상이어야 합니다."
            )

        conn = await Database.get_connection()

        try:
            await conn.start_transaction()

            # 환전 중 해당 유저 행 잠금
            wallet_before = await self._get_wallet_for_update(
                conn,
                discord_id
            )

            total_okpan = (
                wallet_before.get_total_okpan()
            )

            if total_okpan < amount:
                raise RuntimeError(
                    "보유한 옥판이 부족합니다. "
                    f"현재 보유 옥판은 {total_okpan}개입니다."
                )

            remaining_grade1 = wallet_before.grade1
            remaining_grade2 = wallet_before.grade2
            remaining_grade3 = wallet_before.grade3

            exchanged_grade1 = 0
            exchanged_grade2 = 0
            exchanged_grade3 = 0

            # 실제 보유 옥판 중 하나씩 무작위 선택
            for _ in range(amount):

                remaining_total = (
                    remaining_grade1
                    + remaining_grade2
                    + remaining_grade3
                )

                random_number = random.randrange(
                    remaining_total
                )

                if random_number < remaining_grade1:

                    remaining_grade1 -= 1
                    exchanged_grade1 += 1

                elif (
                    random_number
                    < remaining_grade1
                    + remaining_grade2
                ):

                    remaining_grade2 -= 1
                    exchanged_grade2 += 1

                else:

                    remaining_grade3 -= 1
                    exchanged_grade3 += 1

            grade1_money = (
                exchanged_grade1
                * self.GRADE_1_VALUE
            )

            grade2_money = (
                exchanged_grade2
                * self.GRADE_2_VALUE
            )

            grade3_money = (
                exchanged_grade3
                * self.GRADE_3_VALUE
            )

            received_money = (
                grade1_money
                + grade2_money
                + grade3_money
            )

            sql = """
                UPDATE users
                SET okpan_grade_1 = okpan_grade_1 - %s,
                    okpan_grade_2 = okpan_grade_2 - %s,
                    okpan_grade_3 = okpan_grade_3 - %s,
                    money = money + %s
                WHERE discord_id = %s
            """

            cursor = await conn.cursor()

            try:
                await cursor.execute(
                    sql,
                    (
                        exchanged_grade1,
                        exchanged_grade2,
                        exchanged_grade3,
                        received_money,
                        discord_id
                    )
                )

                if cursor.rowcount != 1:
                    raise RuntimeError(
                        "옥판 환전 정보를 저장하지 못했습니다."
                    )

            finally:
                await cursor.close()

            wallet_after = await self._get_wallet(
                conn,
                discord_id
            )

            await conn.commit()

            return OkpanExchangeResult(
                exchanged_grade1=exchanged_grade1,
                exchanged_grade2=exchanged_grade2,
                exchanged_grade3=exchanged_grade3,
                received_money=received_money,
                wallet_after=wallet_after
            )

        except Exception:
            await conn.rollback()
            raise

        finally:
            await conn.close()

    # ============================================
    # 운영진 옥판 지급
    # ============================================

    async def add_okpan(
        self,
        discord_id: str,
        username: str,
        grade: int,
        amount: int
    ) -> OkpanWallet:

        self._validate_grade(
            grade
        )

        if amount <= 0:
            raise ValueError(
                "지급할 옥판은 1개 이상이어야 합니다."
            )

        grade_column = self._get_grade_column(
            grade
        )

        conn = await Database.get_connection()

        try:
            await conn.start_transaction()

            await self._create_or_update_user(
                conn,
                discord_id,
                username
            )

            # grade_column은 내부에서만 결정되므로
            # SQL 문자열에 직접 넣어도 안전하다.
            sql = f"""
                UPDATE users
                SET {grade_column} = {grade_column} + %s
                WHERE discord_id = %s
            """

            cursor = await conn.cursor()

            try:
                await cursor.execute(
                    sql,
                    (
                        amount,
                        discord_id
                    )
                )

                if cursor.rowcount != 1:
                    raise RuntimeError(
                        "옥판을 지급할 유저를 찾을 수 없습니다."
                    )

            finally:
                await cursor.close()

            wallet = await self._get_wallet(
                conn,
                discord_id
            )

            await conn.commit()

            return wallet

        except Exception:
            await conn.rollback()
            raise

        finally:
            await conn.close()

    # ============================================
    # 운영진 옥판 지급
    # ============================================

    async def remove_okpan(
    self,
    discord_id: str,
    username: str,
    grade: int,
    amount: int
    ) -> OkpanWallet:

        """
        운영진이 특정 등급의 옥판을 차감한다.
        해당 등급의 보유량이 부족하면 아무것도 차감하지 않는다.
        """

        self._validate_grade(grade)

        if amount <= 0:
            raise ValueError(
                "차감할 옥판은 1개 이상이어야 합니다."
            )

        grade_column = self._get_grade_column(
            grade
        )

        conn = await Database.get_connection()

        try:
            await conn.start_transaction()

            await self._create_or_update_user(
                conn,
                discord_id,
                username
            )

            sql = f"""
                UPDATE users
                SET {grade_column} = {grade_column} - %s
                WHERE discord_id = %s
                AND {grade_column} >= %s
            """

            cursor = await conn.cursor()

            try:
                await cursor.execute(
                    sql,
                    (
                        amount,
                        discord_id,
                        amount
                    )
                )

                if cursor.rowcount != 1:
                    raise RuntimeError(
                        "해당 등급의 옥판이 부족하여 "
                        "차감하지 못했습니다."
                    )

            finally:
                await cursor.close()

            wallet = await self._get_wallet(
                conn,
                discord_id
            )

            await conn.commit()

            return wallet

        except Exception:
            await conn.rollback()
            raise

        finally:
            await conn.close()

    # ============================================
    # 유저 생성 / 닉네임 갱신
    # ============================================

    async def _create_or_update_user(
        self,
        conn,
        discord_id: str,
        username: str
    ) -> None:

        sql = """
            INSERT INTO users (
                discord_id,
                username,
                money
            )
            VALUES (%s, %s, 0)
            ON DUPLICATE KEY UPDATE
                username = VALUES(username)
        """

        cursor = await conn.cursor()

        try:
            await cursor.execute(
                sql,
                (
                    discord_id,
                    username
                )
            )

        finally:
            await cursor.close()

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
                return OkpanWallet(
                    money=row["money"],
                    grade1=row["okpan_grade_1"],
                    grade2=row["okpan_grade_2"],
                    grade3=row["okpan_grade_3"]
                )

        finally:
            await cursor.close()

        raise RuntimeError(
            "유저의 지갑 정보를 찾을 수 없습니다."
        )

    # ============================================
    # 잠금 상태로 지갑 조회
    # ============================================

    async def _get_wallet_for_update(
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
                return OkpanWallet(
                    money=row["money"],
                    grade1=row["okpan_grade_1"],
                    grade2=row["okpan_grade_2"],
                    grade3=row["okpan_grade_3"]
                )

        finally:
            await cursor.close()

        raise RuntimeError(
            "유저의 지갑 정보를 찾을 수 없습니다."
        )

    # ============================================
    # 등급 컬럼
    # ============================================

    def _get_grade_column(
        self,
        grade: int
    ) -> str:

        self._validate_grade(
            grade
        )

        columns = {
            1: "okpan_grade_1",
            2: "okpan_grade_2",
            3: "okpan_grade_3",
        }

        return columns[grade]

    # ============================================
    # 등급 검증
    # ============================================

    def _validate_grade(
        self,
        grade: int
    ) -> None:

        if grade not in (1, 2, 3):
            raise ValueError(
                "옥판 등급은 1등급부터 3등급까지만 가능합니다."
            )