import discord
from discord import app_commands
from discord.ext import commands

from services.okpan_service import OkpanService
from services.log_service import LogService


class AdminOkpanCommand(commands.Cog):

    def __init__(
        self,
        bot: commands.Bot
    ):
        self.bot = bot

        self.okpan_service = OkpanService()
        self.log_service = LogService()

    # ============================================
    # /옥판지급
    # ============================================

    @app_commands.command(
        name="옥판지급",
        description="운영진이 유저에게 옥판을 지급합니다."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    @app_commands.describe(
        대상="옥판을 지급할 유저",
        등급="지급할 옥판의 내부 등급",
        개수="지급할 옥판 개수",
        사유="옥판 지급 사유"
    )
    @app_commands.choices(
        등급=[
            app_commands.Choice(
                name="1등급",
                value=1
            ),
            app_commands.Choice(
                name="2등급",
                value=2
            ),
            app_commands.Choice(
                name="3등급",
                value=3
            )
        ]
    )
    async def add_okpan(
        self,
        interaction: discord.Interaction,
        대상: discord.Member,
        등급: app_commands.Choice[int],
        개수: int,
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
        # 개수 검사
        # ========================================

        if 개수 <= 0:

            await interaction.response.send_message(
                "지급할 옥판은 1개 이상이어야 합니다.",
                ephemeral=True
            )

            return

        try:

            grade = 등급.value

            # ====================================
            # 옥판 지급
            # ====================================

            wallet = (
                await self.okpan_service.add_okpan(
                    str(대상.id),
                    대상.display_name,
                    grade,
                    개수
                )
            )

            # ====================================
            # 지급 완료 Embed
            # ====================================
            #
            # 내부 등급은 일반 채널에 공개하지 않는다.

            embed = discord.Embed(
                title="🀄 옥판 지급 완료",
                color=discord.Color.green()
            )

            embed.add_field(
                name="👤 대상",
                value=대상.mention,
                inline=True
            )

            embed.add_field(
                name="🀄 지급 수량",
                value=f"**{개수:,}개**",
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
            #
            # 내부 등급은 로그에서만 확인한다.

            await self.log_service.send_admin_okpan_add_log(
                self.bot,
                interaction.user,
                대상,
                grade,
                개수,
                wallet.get_total_okpan(),
                사유
            )

        except (ValueError, RuntimeError) as e:

            await interaction.response.send_message(
                str(e),
                ephemeral=True
            )

        except Exception as e:

            print(
                f"[옥판지급 오류] {e}"
            )

            if interaction.response.is_done():

                await interaction.followup.send(
                    "옥판을 지급하는 중 오류가 발생했습니다.",
                    ephemeral=True
                )

            else:

                await interaction.response.send_message(
                    "옥판을 지급하는 중 오류가 발생했습니다.",
                    ephemeral=True
                )

    # ============================================
    # /옥판차감
    # ============================================

    @app_commands.command(
        name="옥판차감",
        description="운영진이 유저의 옥판을 차감합니다."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    @app_commands.describe(
        대상="옥판을 차감할 유저",
        등급="차감할 옥판의 내부 등급",
        개수="차감할 옥판 개수",
        사유="옥판 차감 사유"
    )
    @app_commands.choices(
        등급=[
            app_commands.Choice(
                name="1등급",
                value=1
            ),
            app_commands.Choice(
                name="2등급",
                value=2
            ),
            app_commands.Choice(
                name="3등급",
                value=3
            )
        ]
    )
    async def remove_okpan(
        self,
        interaction: discord.Interaction,
        대상: discord.Member,
        등급: app_commands.Choice[int],
        개수: int,
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
        # 개수 검사
        # ========================================

        if 개수 <= 0:

            await interaction.response.send_message(
                "차감할 옥판은 1개 이상이어야 합니다.",
                ephemeral=True
            )

            return

        try:

            grade = 등급.value

            # ====================================
            # 옥판 차감
            # ====================================

            wallet = (
                await self.okpan_service.remove_okpan(
                    str(대상.id),
                    대상.display_name,
                    grade,
                    개수
                )
            )

            # ====================================
            # 차감 완료 Embed
            # ====================================
            #
            # 차감된 내부 등급은 공개하지 않는다.

            embed = discord.Embed(
                title="🀄 옥판 차감 완료",
                color=discord.Color.red()
            )

            embed.add_field(
                name="👤 대상",
                value=대상.mention,
                inline=True
            )

            embed.add_field(
                name="🀄 차감 수량",
                value=f"**{개수:,}개**",
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

            await self.log_service.send_admin_okpan_remove_log(
                self.bot,
                interaction.user,
                대상,
                grade,
                개수,
                wallet.get_total_okpan(),
                사유
            )

        except (ValueError, RuntimeError) as e:

            await interaction.response.send_message(
                str(e),
                ephemeral=True
            )

        except Exception as e:

            print(
                f"[옥판차감 오류] {e}"
            )

            if interaction.response.is_done():

                await interaction.followup.send(
                    "옥판을 차감하는 중 오류가 발생했습니다.",
                    ephemeral=True
                )

            else:

                await interaction.response.send_message(
                    "옥판을 차감하는 중 오류가 발생했습니다.",
                    ephemeral=True
                )


# ============================================
# Cog 등록
# ============================================

async def setup(
    bot: commands.Bot
):
    await bot.add_cog(
        AdminOkpanCommand(bot)
    )