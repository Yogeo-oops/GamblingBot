import discord
from discord import app_commands
from discord.ext import commands

from services.okpan_service import OkpanService
from utils.money_util import format_money


class WalletCommand(commands.Cog):

    def __init__(
        self,
        bot: commands.Bot
    ):
        self.bot = bot
        self.okpan_service = OkpanService()

    # ============================================
    # /지갑
    # ============================================

    @app_commands.command(
        name="지갑",
        description="현재 보유 중인 돈과 옥판을 확인합니다."
    )
    async def 지갑(
        self,
        interaction: discord.Interaction
    ):

        discord_id = str(
            interaction.user.id
        )

        if isinstance(
            interaction.user,
            discord.Member
        ):
            username = (
                interaction.user.display_name
            )
        else:
            username = (
                interaction.user.name
            )

        try:

            wallet = (
                await self.okpan_service.get_or_create_wallet(
                    discord_id,
                    username
                )
            )

            # ====================================
            # Embed 생성
            # ====================================

            embed = discord.Embed(
                title="💰 현재 지갑",
                description="\n",
                color=discord.Color.from_rgb(
                    241,
                    196,
                    15
                )
            )

            embed.add_field(
                name="보유 금액",
                value=(
                    f"**{format_money(wallet.money)}**"
                ),
                inline=True
            )

            embed.add_field(
                name="보유 옥판",
                value=(
                    f"**{wallet.get_total_okpan():,}개**"
                ),
                inline=True
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

        except Exception as e:

            print(
                f"[지갑 조회 오류] {e}"
            )

            await interaction.response.send_message(
                "지갑을 불러오는 중 오류가 발생했습니다.",
                ephemeral=True
            )