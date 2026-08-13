import discord
from discord import app_commands
from discord.ext import commands


class HelpCommand(commands.Cog):

    def __init__(
        self,
        bot: commands.Bot
    ):
        self.bot = bot

    # ============================================
    # /도움말
    # ============================================

    @app_commands.command(
        name="도움말",
        description="봇의 명령어와 기능을 확인합니다."
    )
    async def help(
        self,
        interaction: discord.Interaction
    ):

        embed = discord.Embed(
            title="📖 도움말",
            description=(
                "도박 시스템에서 사용할 수 있는 "
                "명령어 목록입니다."
            ),
            color=discord.Color.gold()
        )

        # ========================================
        # 게임
        # ========================================

        embed.add_field(
            name="🎲 게임",
            value=(
                "`/홀짝`\n"
                "ㆍ홀 또는 짝을 맞히는 게임\n\n"

                "`/윷놀이`\n"
                "ㆍ윷 결과에 따라 지급 배율 결정\n\n"

                "`/숫자맞추기`\n"
                "ㆍ1~100 사이의 숫자를 "
                "7번 안에 맞히기\n\n"

                "`/숫자`\n"
                "ㆍ진행 중인 숫자 맞추기에 "
                "숫자 입력\n\n"

                "`/숫자포기`\n"
                "ㆍ진행 중인 숫자 맞추기 포기"
            ),
            inline=False
        )

        # ========================================
        # 재화
        # ========================================

        embed.add_field(
            name="💰 재화",
            value=(
                "`/지갑`\n"
                "ㆍ현재 돈과 옥판 확인\n\n"

                "`/전적`\n"
                "ㆍ도박 전적 확인\n\n"

                "`/옥판구매`\n"
                "ㆍ100문당 옥판 1개 구매\n\n"

                "`/옥판환전`\n"
                "ㆍ보유한 옥판을 돈으로 환전"
            ),
            inline=False
        )

        # ========================================
        # 상점
        # ========================================

        embed.add_field(
            name="🏪 상점",
            value=(
                "`/주막`\n"
                "ㆍ음식과 주류 구매\n\n"

                "`/만물점`\n"
                "ㆍ잡화와 장신구 구매"
            ),
            inline=False
        )

        # ========================================
        # 운영진
        # ========================================
        #
        # 서버 관리 권한이 있는 사람에게만
        # 운영진 명령어를 표시한다.

        if (
            isinstance(
                interaction.user,
                discord.Member
            )
            and interaction.user
            .guild_permissions
            .manage_guild
        ):

            embed.add_field(
                name="👑 운영진 전용",
                value=(
                    "`/돈지급`\n"
                    "ㆍ유저에게 돈 지급\n\n"

                    "`/돈차감`\n"
                    "ㆍ유저의 돈 차감\n\n"

                    "`/옥판지급`\n"
                    "ㆍ유저에게 옥판 지급\n\n"

                    "`/옥판차감`\n"
                    "ㆍ유저의 옥판 차감"
                ),
                inline=False
            )

        embed.set_footer(
            text="\n행운은 준비된 자의 편입니다."
        )

        # ========================================
        # 도움말 전송
        # ========================================

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


# ============================================
# Cog 등록
# ============================================

async def setup(
    bot: commands.Bot
):
    await bot.add_cog(
        HelpCommand(bot)
    )