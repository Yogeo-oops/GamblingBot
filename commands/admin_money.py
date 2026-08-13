import discord
from discord import app_commands
from discord.ext import commands

from services.wallet_service import WalletService
from services.log_service import LogService
from utils.money_util import format_money


class AdminMoneyCommand(commands.Cog):

    def __init__(
        self,
        bot: commands.Bot
    ):
        self.bot = bot

        self.wallet_service = WalletService()
        self.log_service = LogService()

    # ============================================
    # /돈지급
    # ============================================

    @app_commands.command(
        name="돈지급",
        description="운영진이 유저에게 돈을 지급합니다."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    @app_commands.describe(
        대상="돈을 지급할 유저",
        금액="지급할 금액을 입력하세요.",
        사유="돈을 지급하는 이유를 입력하세요."
    )
    async def add_money(
        self,
        interaction: discord.Interaction,
        대상: discord.Member,
        금액: int,
        사유: str = "사유 없음"
    ):

        # ========================================
        # 운영진 권한 확인
        # ========================================

        if (
            not isinstance(
                interaction.user,
                discord.Member
            )
            or not interaction.user.guild_permissions.manage_guild
        ):

            await interaction.response.send_message(
                "이 명령어는 운영진만 사용할 수 있습니다.",
                ephemeral=True
            )

            return

        # ========================================
        # 금액 검사
        # ========================================

        if 금액 <= 0:

            await interaction.response.send_message(
                "지급 금액은 1문 이상이어야 합니다.",
                ephemeral=True
            )

            return

        try:

            # ====================================
            # 돈 지급
            # ====================================

            new_balance = (
                await self.wallet_service.add_money(
                    str(대상.id),
                    대상.display_name,
                    금액
                )
            )

            # ====================================
            # 지급 완료 Embed
            # ====================================

            embed = discord.Embed(
                title="💰 돈 지급 완료",
                color=discord.Color.green()
            )

            embed.add_field(
                name="👤 대상",
                value=대상.mention,
                inline=True
            )

            embed.add_field(
                name="💰 지급 금액",
                value=(
                    f"**{format_money(금액)}**"
                ),
                inline=True
            )

            embed.add_field(
                name="📝 사유",
                value=사유,
                inline=False
            )

            embed.set_footer(
                text=(
                    f"처리: "
                    f"{interaction.user.display_name}"
                )
            )

            await interaction.response.send_message(
                embed=embed
            )

            # ====================================
            # 운영 로그
            # ====================================

            await self.log_service.send_money_add_log(
                self.bot,
                interaction.user,
                대상,
                금액,
                new_balance,
                사유
            )

        except ValueError as e:

            await interaction.response.send_message(
                str(e),
                ephemeral=True
            )

        except Exception as e:

            print(
                f"[돈지급 오류] {e}"
            )

            if interaction.response.is_done():

                await interaction.followup.send(
                    "돈을 지급하는 중 오류가 발생했습니다.",
                    ephemeral=True
                )

            else:

                await interaction.response.send_message(
                    "돈을 지급하는 중 오류가 발생했습니다.",
                    ephemeral=True
                )

    # ============================================
    # /돈차감
    # ============================================

    @app_commands.command(
        name="돈차감",
        description="운영진이 유저의 돈을 차감합니다."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    @app_commands.describe(
        대상="돈을 차감할 유저",
        금액="차감할 금액을 입력하세요.",
        사유="돈을 차감하는 이유를 입력하세요."
    )
    async def remove_money(
        self,
        interaction: discord.Interaction,
        대상: discord.Member,
        금액: int,
        사유: str = "사유 없음"
    ):

        # ========================================
        # 운영진 권한 확인
        # ========================================

        if (
            not isinstance(
                interaction.user,
                discord.Member
            )
            or not interaction.user.guild_permissions.manage_guild
        ):

            await interaction.response.send_message(
                "이 명령어는 운영진만 사용할 수 있습니다.",
                ephemeral=True
            )

            return

        # ========================================
        # 금액 검사
        # ========================================

        if 금액 <= 0:

            await interaction.response.send_message(
                "차감 금액은 1문 이상이어야 합니다.",
                ephemeral=True
            )

            return

        try:

            # ====================================
            # 돈 차감
            # ====================================

            success = (
                await self.wallet_service.remove_money(
                    str(대상.id),
                    대상.display_name,
                    금액
                )
            )

            # ====================================
            # 소지금 부족
            # ====================================

            if not success:

                await interaction.response.send_message(
                    (
                        f"{대상.mention}님의 "
                        "소지금이 부족합니다."
                    ),
                    ephemeral=True
                )

                return

            # ====================================
            # 차감 후 잔액 조회
            # ====================================

            new_balance = (
                await self.wallet_service.get_money(
                    str(대상.id)
                )
            )

            # ====================================
            # 차감 완료 Embed
            # ====================================

            embed = discord.Embed(
                title="💸 돈 차감 완료",
                color=discord.Color.red()
            )

            embed.add_field(
                name="👤 대상",
                value=대상.mention,
                inline=True
            )

            embed.add_field(
                name="💸 차감 금액",
                value=(
                    f"**{format_money(금액)}**"
                ),
                inline=True
            )

            embed.add_field(
                name="📝 사유",
                value=사유,
                inline=False
            )

            embed.set_footer(
                text=(
                    f"처리: "
                    f"{interaction.user.display_name}"
                )
            )

            await interaction.response.send_message(
                embed=embed
            )

            # ====================================
            # 운영 로그
            # ====================================

            await self.log_service.send_money_remove_log(
                self.bot,
                interaction.user,
                대상,
                금액,
                new_balance,
                사유
            )

        except ValueError as e:

            await interaction.response.send_message(
                str(e),
                ephemeral=True
            )

        except Exception as e:

            print(
                f"[돈차감 오류] {e}"
            )

            if interaction.response.is_done():

                await interaction.followup.send(
                    "돈을 차감하는 중 오류가 발생했습니다.",
                    ephemeral=True
                )

            else:

                await interaction.response.send_message(
                    "돈을 차감하는 중 오류가 발생했습니다.",
                    ephemeral=True
                )


# ============================================
# Cog 등록
# ============================================

async def setup(
    bot: commands.Bot
):
    await bot.add_cog(
        AdminMoneyCommand(bot)
    )