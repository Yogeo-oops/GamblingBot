import random

from database import Database
from models.okpan_exchange_result import OkpanExchangeResult
from models.okpan_wallet import OkpanWallet


class OkpanService:
    """
    옥판 구매, 환전, 운영진 지급/차감,
    지갑 조회를 담당한다.

    SQLite 기반으로 동작한다.
    """

    # ============================================
    # 옥판 가격
    # ============================================

    # 돈으로 구매할 때
    # 옥판 1개 = 100문
    OKPAN_PURCHASE_PRICE = 100

    # ============================================
    # 내부 등급별 환전 가치
    # ============================================
    #
    # 1등급 = 기본 가격의 20배
    # 2등급 = 기본 가격의 1배
    # 3등급 = 기본 가격의 0.2배

    GRADE_1_VALUE = 2_000
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

            await conn.execute(
                "BEGIN IMMEDIATE"
            )

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

    # ============================================
    # 지갑 조회
    # ============================================

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

            await conn.execute(
                "BEGIN IMMEDIATE"
            )

            # 유저 생성 / 닉네임 갱신
            await self._create_or_update_user(
                conn,
                discord_id,
                username
            )

            # ====================================
            # 돈 차감 + 2등급 옥판 지급
            # ====================================
            #
            # 돈으로 구매한 옥판은
            # 전부 내부적으로 2등급이다.

            cursor = await conn.execute(
                """
                UPDATE users
                SET money = money - ?,
                    okpan_grade_2 = okpan_grade_2 + ?
                WHERE discord_id = ?
                  AND money >= ?
                """,
                (
                    cost,
                    amount,
                    discord_id,
                    cost
                )
            )

            success = (
                cursor.rowcount == 1
            )

            await cursor.close()

            if not success:

                raise RuntimeError(
                    "옥판을 구매하기 위한 돈이 부족합니다."
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

            # SQLite에는 MySQL의 FOR UPDATE가 없으므로
            # BEGIN IMMEDIATE로 쓰기 트랜잭션을 잠근다.
            await conn.execute(
                "BEGIN IMMEDIATE"
            )

            wallet_before = await self._get_wallet(
                conn,
                discord_id
            )

            total_okpan = (
                wallet_before.get_total_okpan()
            )

            if total_okpan < amount:

                raise RuntimeError(
                    "보유한 옥판이 부족합니다. "
                    f"현재 보유 옥판은 "
                    f"{total_okpan:,}개입니다."
                )

            # ====================================
            # 현재 등급별 보유량
            # ====================================

            remaining_grade1 = (
                wallet_before.grade1
            )

            remaining_grade2 = (
                wallet_before.grade2
            )

            remaining_grade3 = (
                wallet_before.grade3
            )

            exchanged_grade1 = 0
            exchanged_grade2 = 0
            exchanged_grade3 = 0

            # ====================================
            # 실제 보유 옥판 중 무작위 선택
            # ====================================

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

            # ====================================
            # 환전 금액 계산
            # ====================================

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

            # ====================================
            # 옥판 차감 + 돈 지급
            # ====================================

            cursor = await conn.execute(
                """
                UPDATE users
                SET okpan_grade_1 = okpan_grade_1 - ?,
                    okpan_grade_2 = okpan_grade_2 - ?,
                    okpan_grade_3 = okpan_grade_3 - ?,
                    money = money + ?
                WHERE discord_id = ?
                """,
                (
                    exchanged_grade1,
                    exchanged_grade2,
                    exchanged_grade3,
                    received_money,
                    discord_id
                )
            )

            if cursor.rowcount != 1:

                await cursor.close()

                raise RuntimeError(
                    "옥판 환전 정보를 저장하지 못했습니다."
                )

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

        grade_column = (
            self._get_grade_column(
                grade
            )
        )

        conn = await Database.get_connection()

        try:

            await conn.execute(
                "BEGIN IMMEDIATE"
            )

            await self._create_or_update_user(
                conn,
                discord_id,
                username
            )

            # grade_column은 내부에서
            # 허용된 3개 컬럼 중 하나만 반환한다.
            cursor = await conn.execute(
                f"""
                UPDATE users
                SET {grade_column}
                    = {grade_column} + ?
                WHERE discord_id = ?
                """,
                (
                    amount,
                    discord_id
                )
            )

            if cursor.rowcount != 1:

                await cursor.close()

                raise RuntimeError(
                    "옥판을 지급할 유저를 찾을 수 없습니다."
                )

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
    # 운영진 옥판 차감
    # ============================================

    async def remove_okpan(
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
                "차감할 옥판은 1개 이상이어야 합니다."
            )

        grade_column = (
            self._get_grade_column(
                grade
            )
        )

        conn = await Database.get_connection()

        try:

            await conn.execute(
                "BEGIN IMMEDIATE"
            )

            await self._create_or_update_user(
                conn,
                discord_id,
                username
            )

            # ====================================
            # 해당 등급 옥판이 충분할 때만 차감
            # ====================================

            cursor = await conn.execute(
                f"""
                UPDATE users
                SET {grade_column}
                    = {grade_column} - ?
                WHERE discord_id = ?
                  AND {grade_column} >= ?
                """,
                (
                    amount,
                    discord_id,
                    amount
                )
            )

            success = (
                cursor.rowcount == 1
            )

            await cursor.close()

            if not success:

                raise RuntimeError(
                    "해당 등급의 옥판이 부족합니다."
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

    # ============================================
    # 유저 생성 / 닉네임 갱신
    # ============================================

    async def _create_or_update_user(
        self,
        conn,
        discord_id: str,
        username: str
    ) -> None:

        await conn.execute(
            """
            INSERT INTO users (
                discord_id,
                username,
                money
            )
            VALUES (?, ?, 0)

            ON CONFLICT(discord_id)
            DO UPDATE SET
                username = excluded.username
            """,
            (
                discord_id,
                username
            )
        )

    # ============================================
    # 내부 지갑 조회
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
                "유저의 지갑 정보를 찾을 수 없습니다."
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

    # ============================================
    # 등급별 DB 컬럼
    # ============================================

    def _get_grade_column(
        self,
        grade: int
    ) -> str:

        self._validate_grade(
            grade
        )

        if grade == 1:
            return "okpan_grade_1"

        if grade == 2:
            return "okpan_grade_2"

        return "okpan_grade_3"

    # ============================================
    # 등급 검사
    # ============================================

    def _validate_grade(
        self,
        grade: int
    ) -> None:

        if grade not in (
            1,
            2,
            3
        ):

            raise ValueError(
                "옥판 등급은 1등급부터 "
                "3등급까지만 가능합니다."
            )