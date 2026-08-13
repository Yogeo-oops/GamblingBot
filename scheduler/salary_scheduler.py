import os
from datetime import time
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from services.salary_service import SalaryService
from utils.money_util import format_money


load_dotenv()


class SalaryScheduler(commands.Cog):
    """
    매일 자정에 일급 지급을 실행한다.

    봇 시작 시에도 한 번 지급 여부를 확인하고,
    실제 지급된 유저가 있을 때만 지정 채널에 공지한다.
    """

    KOREA_ZONE = ZoneInfo("Asia/Seoul")

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.salary_service = SalaryService()

        # Cog가 생성되면 스케줄러 시작
        self.daily_salary.start()

    # ============================================
    # 매일 00:00 KST 실행
    # ============================================

    @tasks.loop(
        time=time(
            hour=0,
            minute=0,
            tzinfo=KOREA_ZONE
        )
    )
    async def daily_salary(self):
        await self._run_salary_payment()

    # ============================================
    # 스케줄러 시작 전 봇 준비 대기
    # ============================================

    @daily_salary.before_loop
    async def before_daily_salary(self):
        await self.bot.wait_until_ready()

    # ============================================
    # 실제 월급 지급
    # ============================================

    async def _run_salary_payment(self) -> None:

        try:
            paid_user_count = (
                await self.salary_service.pay_daily_salary()
            )

            # 실제 지급된 사람이 있을 때만 공지
            if paid_user_count > 0:
                await self._send_salary_message(
                    paid_user_count
                )

        except Exception as e:
            print(
                f"[일급 지급 오류] {e}"
            )

    # ============================================
    # 일급 지급 공지
    # ============================================

    async def _send_salary_message(
        self,
        paid_user_count: int
    ) -> None:

        channel_id = os.getenv(
            "SALARY_CHANNEL_ID"
        )

        if not channel_id:
            return

        try:
            channel_id_int = int(
                channel_id
            )

        except ValueError:
            print(
                "SALARY_CHANNEL_ID가 "
                "올바른 숫자 형식이 아닙니다."
            )
            return

        channel = self.bot.get_channel(
            channel_id_int
        )

        if not isinstance(
            channel,
            discord.TextChannel
        ):
            print(
                "일급 공지 채널을 찾을 수 없습니다."
            )
            return

        salary_amount_text = os.getenv(
            "SALARY_AMOUNT",
            "0"
        )

        try:
            salary_amount = int(
                salary_amount_text
            )

        except ValueError:
            print(
                "SALARY_AMOUNT가 "
                "올바른 숫자 형식이 아닙니다."
            )
            return

        total_amount = (
            salary_amount
            * paid_user_count
        )

        await channel.send(
            f"""
💰 오늘의 일급 지급이 완료되었습니다.

지급 인원: {paid_user_count:,}명
1인 지급액: {format_money(salary_amount)}
총 지급액: {format_money(total_amount)}
            """.strip()
        )

    # ============================================
    # Cog 종료 시 스케줄러 종료
    # ============================================

    def cog_unload(self):
        self.daily_salary.cancel()


async def setup(
    bot: commands.Bot
):
    scheduler = SalaryScheduler(bot)

    await bot.add_cog(
        scheduler
    )