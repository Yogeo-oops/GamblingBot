import asyncio

import discord
from discord import app_commands
from discord.ext import commands

from services.gamble_service import GambleService


class OddEvenCommand(commands.Cog):

    RESULT_DELAY_SECONDS = 2

    def __init__(
        self,
        bot: commands.Bot
    ):
        self.bot = bot

        # 홀짝 게임 처리 서비스
        self.gamble_service = GambleService()

    # ============================================
    # /홀짝
    # ============================================

    @app_commands.command(
        name="홀짝",
        description="홀 또는 짝을 맞히는 도박 게임입니다."
    )
    @app_commands.describe(
        선택="홀 또는 짝을 선택하세요.",
        배팅옥판="배팅할 옥판 개수를 입력하세요."
    )
    @app_commands.choices(
        선택=[
            app_commands.Choice(
                name="홀",
                value="홀"
            ),
            app_commands.Choice(
                name="짝",
                value="짝"
            )
        ]
    )
    async def odd_even(
        self,
        interaction: discord.Interaction,
        선택: app_commands.Choice[str],
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

        user_choice = 선택.value
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
            # 게임 진행 과정은 본인에게만 표시한다.

            await interaction.response.defer(
                ephemeral=True
            )

            progress_embed = discord.Embed(
                title="🎲 홀짝",
                description="주사위를 굴리는 중입니다...",
                color=discord.Color.gold()
            )

            progress_embed.add_field(
                name="선택",
                value=f"**{user_choice}**",
                inline=True
            )

            progress_embed.add_field(
                name="배팅",
                value=f"**{배팅옥판:,}개**",
                inline=True
            )

            progress_embed.set_footer(
                text="결과를 확인하고 있습니다..."
            )

            await interaction.edit_original_response(
                embed=progress_embed
            )

            # ====================================
            # 결과 연출 대기
            # ====================================

            await asyncio.sleep(
                self.RESULT_DELAY_SECONDS
            )

            # ====================================
            # 실제 홀짝 게임 실행
            # ====================================

            result = (
                await self.gamble_service.play_odd_even(
                    discord_id,
                    username,
                    user_choice,
                    배팅옥판
                )
            )

            # ====================================
            # 승리
            # ====================================

            if result.win:

                result_embed = discord.Embed(
                    title="🎉 홀짝 승리!",
                    description=(
                        f"{interaction.user.mention}님이 "
                        "홀짝에서 승리했습니다."
                    ),
                    color=discord.Color.green()
                )

                result_embed.add_field(
                    name="🎯 선택",
                    value=f"**{user_choice}**",
                    inline=True
                )

                result_embed.add_field(
                    name="🎲 결과",
                    value=f"**{result.bot_choice}**",
                    inline=True
                )

                result_embed.add_field(
                    name="\u200b",
                    value="\u200b",
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

            # ====================================
            # 패배
            # ====================================

            else:

                result_embed = discord.Embed(
                    title="💸 홀짝 패배",
                    description=(
                        f"{interaction.user.mention}님이 "
                        "홀짝에서 패배했습니다."
                    ),
                    color=discord.Color.red()
                )

                result_embed.add_field(
                    name="🎯 선택",
                    value=f"**{user_choice}**",
                    inline=True
                )

                result_embed.add_field(
                    name="🎲 결과",
                    value=f"**{result.bot_choice}**",
                    inline=True
                )

                result_embed.add_field(
                    name="\u200b",
                    value="\u200b",
                    inline=False
                )

                result_embed.add_field(
                    name="🀄 배팅",
                    value=f"**{배팅옥판:,}개**",
                    inline=True
                )

                result_embed.add_field(
                    name="💸 손실",
                    value=f"**-{배팅옥판:,}개**",
                    inline=True
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
        # 입력 / 옥판 부족 등의 오류
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
                f"[홀짝 게임 오류] {e}"
            )

            message = (
                "홀짝 게임을 처리하는 중 오류가 발생했습니다."
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
        OddEvenCommand(bot)
    )