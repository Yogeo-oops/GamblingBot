import os

from datetime import datetime
from zoneinfo import ZoneInfo

from database import Database


class SalaryService:
    """
    일일 월급 지급을 담당한다.

    SQLite 기반으로 동작한다.
    """

    KOREA_ZONE = ZoneInfo(
        "Asia/Seoul"
    )

    # ============================================
    # 오늘 일급 지급
    # ============================================

    async def pay_daily_salary(
        self
    ) -> int:

        # ========================================
        # 환경변수에서 지급 금액 조회
        # ========================================

        salary_value = os.getenv(
            "SALARY_AMOUNT"
        )

        if not salary_value:

            raise RuntimeError(
                "환경변수에 SALARY_AMOUNT가 없습니다."
            )

        try:

            salary_amount = int(
                salary_value
            )

        except ValueError:

            raise RuntimeError(
                "SALARY_AMOUNT는 숫자여야 합니다."
            )

        if salary_amount <= 0:

            raise RuntimeError(
                "SALARY_AMOUNT는 1 이상의 숫자여야 합니다."
            )

        # ========================================
        # 오늘 날짜
        # ========================================
        #
        # YYYY-MM-DD 형식으로 저장한다.
        #
        # SQLite에는 별도의 DATE 타입이 없어도
        # ISO 날짜 문자열이면 비교가 가능하다.

        today = (
            datetime.now(
                self.KOREA_ZONE
            )
            .date()
            .isoformat()
        )

        conn = (
            await Database.get_connection()
        )

        try:

            await conn.execute(
                "BEGIN IMMEDIATE"
            )

            # ====================================
            # 오늘 아직 일급을 받지 않은 유저에게 지급
            # ====================================

            cursor = await conn.execute(
                """
                UPDATE users
                SET money = money + ?,
                    last_salary_date = ?
                WHERE last_salary_date IS NULL
                   OR last_salary_date < ?
                """,
                (
                    salary_amount,
                    today,
                    today
                )
            )

            paid_user_count = (
                cursor.rowcount
            )

            await cursor.close()

            await conn.commit()

            return paid_user_count

        except Exception:

            await conn.rollback()
            raise

        finally:

            await conn.close()