import discord
from discord import app_commands
from discord.ext import commands

from services.gamble_stats_service import GambleStatsService


class GambleStatsCommand(commands.Cog):

    def __init__(
        self,
        bot: commands.Bot
    ):
        self.bot = bot

        self.gamble_stats_service = (
            GambleStatsService()
        )

    # ============================================
    # /전적
    # ============================================

    @app_commands.command(
        name="전적",
        description="자신의 도박 전적을 확인합니다."
    )
    async def 전적(
        self,
        interaction: discord.Interaction
    ):

        discord_id = str(
            interaction.user.id
        )

        try:

            stats = (
                await self.gamble_stats_service.get_stats(
                    discord_id
                )
            )

            # ====================================
            # 승률
            # ====================================

            if stats.total_games > 0:

                win_rate = (
                    stats.total_wins
                    * 100
                    / stats.total_games
                )

            else:

                win_rate = 0.0

            # ====================================
            # 누적 손익
            # ====================================

            profit = (
                stats.total_payout
                - stats.total_bet
            )

            if profit > 0:

                profit_text = (
                    f"+{profit:,}개"
                )

            elif profit < 0:

                profit_text = (
                    f"-{abs(profit):,}개"
                )

            else:

                profit_text = "0개"

            # ====================================
            # Embed
            # ====================================

            embed = discord.Embed(
                title="🎰 도박 전적",
                description=(
                    f"{interaction.user.mention}님의 "
                    "도박 기록입니다."
                ),
                color=discord.Color.from_rgb(
                    155,
                    89,
                    182
                )
            )

            # ====================================
            # 게임 기록
            # ====================================

            embed.add_field(
                name="🎲 게임 기록",
                value=(
                    f"총 게임: 　**{stats.total_games}회**\n"
                    f"승리: 　　 **{stats.total_wins}회**\n"
                    f"패배: 　　 **{stats.total_losses}회**\n"
                    f"승률:　　 **{win_rate:.1f}%**\n\n"
                ),
                inline=False
            )

            embed.add_field(
                name="🀄 옥판 기록",
                value=(
                    f"총 배팅: 　**{stats.total_bet}개**\n"
                    f"총 지급: 　**{stats.total_payout}개**\n"
                    f"손익: 　　 **{profit_text}**\n"
                    f"최고 지급: **{stats.max_payout}개**"
                ),
                inline=False
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

        except Exception as e:

            print(
                f"[전적 조회 오류] {e}"
            )

            await interaction.response.send_message(
                "전적을 불러오는 중 오류가 발생했습니다.",
                ephemeral=True
            )