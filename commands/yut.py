import asyncio

import discord
from discord import app_commands
from discord.ext import commands

from services.gamble_service import GambleService


class YutCommand(commands.Cog):

    RESULT_DELAY_SECONDS = 2

    def __init__(
        self,
        bot: commands.Bot
    ):
        self.bot = bot

        # 윷놀이 처리 서비스
        self.gamble_service = GambleService()

    # ============================================
    # /윷놀이
    # ============================================

    @app_commands.command(
        name="윷놀이",
        description="가중치에 따라 결과가 결정되는 도박 게임입니다."
    )
    @app_commands.describe(
        배팅옥판="배팅할 옥판 개수를 입력하세요."
    )
    async def yut(
        self,
        interaction: discord.Interaction,
        배팅옥판: int
    ):

        # ========================================
        # 배팅 값 검사
        # ========================================

        if 배팅옥판 <= 0:

            await interaction.response.send_message(
                "배팅할 옥판은 1개 이상이어야 합니다.",
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
            # 진행 화면
            # ====================================
            #
            # 게임 진행 과정은 본인에게만 표시

            await interaction.response.defer(
                ephemeral=True
            )

            progress_embed = discord.Embed(
                title="🎲 윷놀이",
                description="윷을 던지고 있습니다...",
                color=discord.Color.gold()
            )

            progress_embed.add_field(
                name="🀄 배팅",
                value=f"**{배팅옥판:,}개**",
                inline=False
            )

            progress_embed.set_footer(
                text="결과를 확인하고 있습니다..."
            )

            await interaction.edit_original_response(
                embed=progress_embed
            )

            # ====================================
            # 결과 연출
            # ====================================

            await asyncio.sleep(
                self.RESULT_DELAY_SECONDS
            )

            # ====================================
            # 실제 게임 실행
            # ====================================

            result = (
                await self.gamble_service.play_yut(
                    discord_id,
                    username,
                    배팅옥판
                )
            )

            outcome = result.outcome

            # ====================================
            # 실제 손익 계산
            # ====================================

            net_change = (
                result.payout_okpan
                - 배팅옥판
            )

            if net_change > 0:

                change_text = (
                    f"+{net_change:,}개"
                )

            elif net_change < 0:

                change_text = (
                    f"-{abs(net_change):,}개"
                )

            else:

                change_text = "0개"

            # 서비스와 동일한 승패 기준
            is_win = (
                result.payout_okpan
                >= 배팅옥판
            )

            # ====================================
            # 승리 결과
            # ====================================

            if is_win:

                result_embed = discord.Embed(
                    title="🎉 윷놀이 승리!",
                    description=(
                        f"{interaction.user.mention}님이 "
                        "윷놀이에서 승리했습니다."
                    ),
                    color=discord.Color.green()
                )

            # ====================================
            # 패배 결과
            # ====================================

            else:

                result_embed = discord.Embed(
                    title="💸 윷놀이 패배",
                    description=(
                        f"{interaction.user.mention}님이 "
                        "윷놀이에서 패배했습니다."
                    ),
                    color=discord.Color.red()
                )

            # ====================================
            # 결과 정보
            # ====================================

            result_embed.add_field(
                name=f"🎲 결과",
                value=
                    f"**{outcome.display_name}** - 배율 **{outcome.multiplier_text}**\n",
                inline=False
            )

            result_embed.add_field(
                name="🀄 배팅",
                value=f"**{배팅옥판:,}개**",
                inline=True
            )

            result_embed.add_field(
                name="✨ 지급",
                value=f"**{result.payout_okpan:,}개**",
                inline=True
            )

            result_embed.add_field(
                name="📊 손익",
                value=f"**{change_text}**",
                inline=False
            )

            # ====================================
            # 개인 진행 화면 삭제
            # ====================================

            try:

                await interaction.delete_original_response()

            except discord.NotFound:

                pass

            # ====================================
            # 최종 결과 공개
            # ====================================

            await interaction.followup.send(
                embed=result_embed,
                ephemeral=False
            )

        # ========================================
        # 옥판 부족 / 입력 오류
        # ========================================

        except (ValueError, RuntimeError) as e:

            if interaction.response.is_done():

                await interaction.edit_original_response(
                    content=str(e),
                    embed=None
                )

            else:

                await interaction.response.send_message(
                    str(e),
                    ephemeral=True
                )

        # ========================================
        # 숫자가 너무 큰 경우
        # ========================================

        except OverflowError:

            message = (
                "배팅한 옥판 개수가 너무 큽니다."
            )

            if interaction.response.is_done():

                await interaction.edit_original_response(
                    content=message,
                    embed=None
                )

            else:

                await interaction.response.send_message(
                    message,
                    ephemeral=True
                )

        # ========================================
        # 기타 오류
        # ========================================

        except Exception as e:

            print(
                f"[윷놀이 오류] {e}"
            )

            message = (
                "윷놀이를 처리하는 중 오류가 발생했습니다."
            )

            if interaction.response.is_done():

                await interaction.edit_original_response(
                    content=message,
                    embed=None
                )

            else:

                await interaction.response.send_message(
                    message,
                    ephemeral=True
                )


async def setup(
    bot: commands.Bot
):
    await bot.add_cog(
        YutCommand(bot)
    )