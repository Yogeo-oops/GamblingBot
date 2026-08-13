import discord
from discord import app_commands
from discord.ext import commands

from services.okpan_service import OkpanService
from services.log_service import LogService
from utils.money_util import format_money


class OkpanCommand(commands.Cog):

    def __init__(
        self,
        bot: commands.Bot
    ):
        self.bot = bot

        self.okpan_service = OkpanService()
        self.log_service = LogService()

    # ============================================
    # /옥판구매
    # ============================================

    @app_commands.command(
        name="옥판구매",
        description="돈을 사용하여 옥판을 구매합니다."
    )
    @app_commands.describe(
        개수="구매할 옥판 개수를 입력하세요."
    )
    async def buy_okpan(
        self,
        interaction: discord.Interaction,
        개수: int
    ):

        if 개수 <= 0:

            await interaction.response.send_message(
                "구매할 옥판은 1개 이상이어야 합니다.",
                ephemeral=True
            )

            return

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

            # ====================================
            # 구매 비용 계산
            # ====================================

            cost = (
                개수
                * self.okpan_service.OKPAN_PURCHASE_PRICE
            )

            # ====================================
            # 실제 구매
            # ====================================

            wallet = (
                await self.okpan_service.buy_okpan(
                    discord_id,
                    username,
                    개수
                )
            )

            # ====================================
            # 구매 완료 Embed
            # ====================================

            embed = discord.Embed(
                title="🀄 옥판 구매 완료",
                description=(
                    f"{interaction.user.mention}님이 "
                    "옥판을 구매했습니다."
                ),
                color=discord.Color.from_rgb(
                    52,
                    152,
                    219
                )
            )

            embed.add_field(
                name="🀄 구매 수량",
                value=f"**{개수:,}개**",
                inline=True
            )

            embed.add_field(
                name="💰 사용 금액",
                value=f"**{format_money(cost)}**",
                inline=True
            )

            await interaction.response.send_message(
                embed=embed
            )

            # ====================================
            # 구매 로그
            # ====================================

            await self.log_service.send_okpan_purchase_log(
                self.bot,
                interaction.user,
                개수,
                cost,
                wallet
            )

        # ========================================
        # 돈 부족 / 입력 오류
        # ========================================

        except (ValueError, RuntimeError) as e:

            await interaction.response.send_message(
                str(e),
                ephemeral=True
            )

        # ========================================
        # 숫자가 너무 큰 경우
        # ========================================

        except OverflowError:

            await interaction.response.send_message(
                "구매하려는 옥판 개수가 너무 큽니다.",
                ephemeral=True
            )

        # ========================================
        # 기타 오류
        # ========================================

        except Exception as e:

            print(
                f"[옥판구매 오류] {e}"
            )

            if interaction.response.is_done():

                await interaction.followup.send(
                    "옥판을 구매하는 중 오류가 발생했습니다.",
                    ephemeral=True
                )

            else:

                await interaction.response.send_message(
                    "옥판을 구매하는 중 오류가 발생했습니다.",
                    ephemeral=True
                )

    # ============================================
    # /옥판환전
    # ============================================

    @app_commands.command(
        name="옥판환전",
        description="보유한 옥판을 돈으로 환전합니다."
    )
    @app_commands.describe(
        개수="환전할 옥판 개수를 입력하세요."
    )
    async def exchange_okpan(
        self,
        interaction: discord.Interaction,
        개수: int
    ):

        if 개수 <= 0:

            await interaction.response.send_message(
                "환전할 옥판은 1개 이상이어야 합니다.",
                ephemeral=True
            )

            return

        try:

            # ====================================
            # 실제 환전
            # ====================================

            result = (
                await self.okpan_service.exchange_random_okpan(
                    str(interaction.user.id),
                    개수
                )
            )

            # ====================================
            # 환전 완료 Embed
            # ====================================

            embed = discord.Embed(
                title="💰 옥판 환전 완료",
                description=(
                    f"{interaction.user.mention}님이 "
                    "옥판을 환전했습니다."
                ),
                color=discord.Color.from_rgb(
                    241,
                    196,
                    15
                )
            )

            embed.add_field(
                name="🀄 환전 수량",
                value=(
                    f"**{result.get_exchanged_total():,}개**"
                ),
                inline=True
            )

            embed.add_field(
                name="💰 지급 금액",
                value=(
                    f"**{format_money(result.received_money)}**"
                ),
                inline=True
            )

            await interaction.response.send_message(
                embed=embed
            )

            # ====================================
            # 환전 로그
            # ====================================

            await self.log_service.send_okpan_exchange_log(
                self.bot,
                interaction.user,
                result
            )

        # ========================================
        # 옥판 부족 / 입력 오류
        # ========================================

        except (ValueError, RuntimeError) as e:

            await interaction.response.send_message(
                str(e),
                ephemeral=True
            )

        # ========================================
        # 금액 범위 초과
        # ========================================

        except OverflowError:

            await interaction.response.send_message(
                "환전 금액이 처리 가능한 범위를 초과했습니다.",
                ephemeral=True
            )

        # ========================================
        # 기타 오류
        # ========================================

        except Exception as e:

            print(
                f"[옥판환전 오류] {e}"
            )

            if interaction.response.is_done():

                await interaction.followup.send(
                    "옥판을 환전하는 중 오류가 발생했습니다.",
                    ephemeral=True
                )

            else:

                await interaction.response.send_message(
                    "옥판을 환전하는 중 오류가 발생했습니다.",
                    ephemeral=True
                )


# ============================================
# Cog 등록
# ============================================

async def setup(
    bot: commands.Bot
):
    await bot.add_cog(
        OkpanCommand(bot)
    )