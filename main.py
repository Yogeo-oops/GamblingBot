import os
import asyncio
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

# ============================================

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(
    dotenv_path=ENV_PATH,
    override=True
)

# ============================================

from commands.wallet import WalletCommand
from commands.admin_money import AdminMoneyCommand
from commands.odd_even import OddEvenCommand
from commands.yut import YutCommand
from commands.number_game import NumberGameCommand
from commands.gamble_stats import GambleStatsCommand
from commands.okpan import OkpanCommand
from commands.admin_okpan import AdminOkpanCommand
from commands.help import HelpCommand
from commands.food_store import FoodStoreCommand
from commands.general_store import GeneralStoreCommand


from scheduler.salary_scheduler import SalaryScheduler

# ============================================
# .env 불러오기
# ============================================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        ".env에 DISCORD_TOKEN이 없습니다."
    )

# ============================================
# Bot
# ============================================

class GamblingBot(commands.Bot):

    def __init__(self):

        intents = discord.Intents.default()

        super().__init__(
            command_prefix="!",
            intents=intents
        )

        # 봇 시작 직후 월급 확인을
        # 한 번만 실행하기 위한 변수
        self.startup_salary_checked = False

        # SalaryScheduler 객체를 저장
        self.salary_scheduler: SalaryScheduler | None = None

    # ============================================
    # 봇 시작 준비
    # ============================================

    async def setup_hook(self):

        # ----------------------------
        # Command 등록
        # ----------------------------

        await self.add_cog(
            WalletCommand(self)
        )

        await self.add_cog(
            AdminMoneyCommand(self)
        )

        await self.add_cog(
            OddEvenCommand(self)
        )

        await self.add_cog(
            YutCommand(self)
        )

        await self.add_cog(
            NumberGameCommand(self)
        )

        await self.add_cog(
            GambleStatsCommand(self)
        )

        await self.add_cog(
            OkpanCommand(self)
        )

        await self.add_cog(
            AdminOkpanCommand(self)
        )

        await self.add_cog(
            HelpCommand(self)
        )

        await self.add_cog(
            FoodStoreCommand(self)
        )

        await self.add_cog(
            GeneralStoreCommand(self)
        )

        # ----------------------------
        # 월급 스케줄러 등록
        # ----------------------------

        self.salary_scheduler = SalaryScheduler(self)

        await self.add_cog(
            self.salary_scheduler
        )

        # ----------------------------
        # 슬래시 명령어 Discord 등록
        # ----------------------------

        synced = await self.tree.sync()

        print("현재 로드된 명령어:")

        for command in self.tree.get_commands():
            print("-", command.name)

        print(
            f"명령어 등록 완료: {len(synced)}개"
        )


# ============================================
# Bot 객체 생성
# ============================================

bot = GamblingBot()


# ============================================
# 봇 준비 완료
# ============================================

@bot.event
async def on_ready():

    print("=" * 40)
    print(f"{bot.user} 로그인 완료")
    print("=" * 40)

    # 봇 실행 시 오늘 일급 지급 여부를 한 번 확인
    if (
        not bot.startup_salary_checked
        and bot.salary_scheduler is not None
    ):
        bot.startup_salary_checked = True

        await bot.salary_scheduler._run_salary_payment()

    print("도박봇 실행 완료!")

# ============================================
# 프로그램 시작
# ============================================

async def main():

    async with bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())