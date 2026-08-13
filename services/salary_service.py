import os
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from database import Database


load_dotenv()


class SalaryService:
    """
    일일 월급 지급을 담당한다.
    """

    # 모든 날짜 계산은 한국 시간을 기준으로 한다.
    KOREA_ZONE = ZoneInfo("Asia/Seoul")

    async def pay_daily_salary(self) -> int:
        """
        오늘 아직 월급을 받지 않은 모든 유저에게 월급을 지급한다.

        Returns:
            실제로 월급을 받은 유저 수
        """

        salary_amount = int(
            os.getenv("SALARY_AMOUNT", "0")
        )

        if salary_amount <= 0:
            raise RuntimeError(
                "SALARY_AMOUNT는 1 이상의 숫자여야 합니다."
            )

        # 현재 한국 날짜
        today = datetime.now(
            self.KOREA_ZONE
        ).date()

        sql = """
            UPDATE users
            SET money = money + %s,
                last_salary_date = %s
            WHERE last_salary_date IS NULL
               OR last_salary_date < %s
        """

        conn = await Database.get_connection()

        try:
            cursor = await conn.cursor()

            try:
                await cursor.execute(
                    sql,
                    (
                        salary_amount,
                        today,
                        today
                    )
                )

                await conn.commit()

                # 실제 월급을 받은 유저 수 반환
                return cursor.rowcount

            finally:
                await cursor.close()

        finally:
            await conn.close()