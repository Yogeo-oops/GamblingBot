import discord
from discord import app_commands
from discord.ext import commands

from models.number_guess_result import NumberGuessStatus
from services.number_game_service import NumberGameService


class NumberGameCommand(commands.Cog):

    MAX_ATTEMPTS = 7

    def __init__(
        self,
        bot: commands.Bot
    ):
        self.bot = bot

        # 숫자맞추기 / 숫자 / 숫자포기 명령어가
        # 같은 서비스 객체를 공유해야 진행 상태도 공유된다.
        self.number_game_service = NumberGameService()

    # ============================================
    # 진행바 생성
    # ============================================

    def _make_progress_bar(
        self,
        attempt_count: int
    ) -> str:

        used = "■" * attempt_count

        remaining = "□" * (
            self.MAX_ATTEMPTS
            - attempt_count
        )

        return used + remaining

    # ============================================
    # /숫자맞추기
    # ============================================

    @app_commands.command(
        name="숫자맞추기",
        description="1부터 100 사이의 숫자를 최대 7번 안에 맞히는 게임입니다."
    )
    @app_commands.describe(
        배팅옥판="배팅할 옥판 개수를 입력하세요."
    )
    async def start_game(
        self,
        interaction: discord.Interaction,
        배팅옥판: int
    ):

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

            result = (
                await self.number_game_service.start_game(
                    discord_id,
                    username,
                    배팅옥판
                )
            )

            # ====================================
            # 게임 시작 Embed
            # ====================================

            embed = discord.Embed(
                title="🔢 숫자 맞추기",
                description=(
                    "1부터 100 사이의 숫자를 맞혀보세요.\n"
                    "최대 **7번**의 기회가 주어집니다."
                ),
                color=discord.Color.gold()
            )

            embed.add_field(
                name="🀄 배팅",
                value=(
                    f"**{result.bet_okpan:,}개**"
                ),
                inline=True
            )

            embed.add_field(
                name="🎯 최대 기회",
                value="**7회**",
                inline=True
            )

            embed.add_field(
                name="📌 숫자 입력",
                value="`/숫자 숫자:50`",
                inline=False
            )

            embed.add_field(
                name="🏳️ 포기",
                value="`/숫자포기`",
                inline=False
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

        except (ValueError, RuntimeError) as e:

            await interaction.response.send_message(
                str(e),
                ephemeral=True
            )

        except Exception as e:

            print(
                f"[숫자맞추기 시작 오류] {e}"
            )

            if interaction.response.is_done():

                await interaction.followup.send(
                    "숫자 맞추기 게임을 시작하는 중 오류가 발생했습니다.",
                    ephemeral=True
                )

            else:

                await interaction.response.send_message(
                    "숫자 맞추기 게임을 시작하는 중 오류가 발생했습니다.",
                    ephemeral=True
                )

    # ============================================
    # /숫자
    # ============================================

    @app_commands.command(
        name="숫자",
        description="진행 중인 숫자 맞추기 게임에 숫자를 입력합니다."
    )
    @app_commands.describe(
        숫자="1부터 100 사이의 숫자를 입력하세요."
    )
    async def guess_number(
        self,
        interaction: discord.Interaction,
        숫자: int
    ):

        discord_id = str(
            interaction.user.id
        )

        try:

            result = (
                await self.number_game_service.guess(
                    discord_id,
                    숫자
                )
            )

            progress_bar = (
                self._make_progress_bar(
                    result.attempt_count
                )
            )

            # ====================================
            # UP
            # ====================================

            if (
                result.status
                == NumberGuessStatus.TOO_LOW
            ):

                embed = discord.Embed(
                    title="📈 UP!",
                    description=(
                        f"정답은 **{숫자}보다 큽니다.**"
                    ),
                    color=discord.Color.gold()
                )

                embed.add_field(
                    name="🎯 진행 상황",
                    value=(
                        f"`{progress_bar}`\n"
                        f"**{result.attempt_count} / "
                        f"{self.MAX_ATTEMPTS}회**"
                    ),
                    inline=False
                )

                embed.add_field(
                    name="남은 기회",
                    value=(
                        f"**{self.MAX_ATTEMPTS - result.attempt_count}회**"
                    ),
                    inline=False
                )

                await interaction.response.send_message(
                    embed=embed,
                    ephemeral=True
                )

                return

            # ====================================
            # DOWN
            # ====================================

            if (
                result.status
                == NumberGuessStatus.TOO_HIGH
            ):

                embed = discord.Embed(
                    title="📉 DOWN!",
                    description=(
                        f"정답은 **{숫자}보다 작습니다.**"
                    ),
                    color=discord.Color.gold()
                )

                embed.add_field(
                    name="🎯 진행 상황",
                    value=(
                        f"`{progress_bar}`\n"
                        f"**{result.attempt_count} / "
                        f"{self.MAX_ATTEMPTS}회**"
                    ),
                    inline=False
                )

                embed.add_field(
                    name="남은 기회",
                    value=(
                        f"**{self.MAX_ATTEMPTS - result.attempt_count}회**"
                    ),
                    inline=False
                )

                await interaction.response.send_message(
                    embed=embed,
                    ephemeral=True
                )

                return

            # ====================================
            # 정답 성공
            # ====================================

            if (
                result.status
                == NumberGuessStatus.CORRECT
            ):

                embed = discord.Embed(
                    title="🎉 숫자 맞추기 성공!",
                    description=(
                        f"{interaction.user.mention}님이 "
                        "정답을 맞혔습니다."
                    ),
                    color=discord.Color.green()
                )

                embed.add_field(
                    name="🎯 정답",
                    value=(
                        f"**{result.answer}**"
                    ),
                    inline=True
                )

                embed.add_field(
                    name="📝 성공 시도",
                    value=(
                        f"**{result.attempt_count} / "
                        f"{self.MAX_ATTEMPTS}회**"
                    ),
                    inline=True
                )

                embed.add_field(
                    name="\u200b",
                    value="\u200b",
                    inline=False
                )

                embed.add_field(
                    name="🀄 배팅",
                    value=(
                        f"**{result.bet_okpan:,}개**"
                    ),
                    inline=True
                )

                embed.add_field(
                    name="✨ 지급",
                    value=(
                        f"**{result.payout_okpan:,}개**"
                    ),
                    inline=True
                )

                await interaction.response.send_message(
                    embed=embed
                )

                return

            # ====================================
            # 7회 실패
            # ====================================

            if (
                result.status
                == NumberGuessStatus.FAILED
            ):

                embed = discord.Embed(
                    title="💸 숫자 맞추기 실패",
                    description=(
                        f"{interaction.user.mention}님이 "
                        "7번의 기회를 모두 사용했습니다."
                    ),
                    color=discord.Color.red()
                )

                embed.add_field(
                    name="🎯 정답",
                    value=(
                        f"**{result.answer}**"
                    ),
                    inline=True
                )

                embed.add_field(
                    name="📝 사용한 기회",
                    value=(
                        f"**{result.attempt_count} / "
                        f"{self.MAX_ATTEMPTS}회**"
                    ),
                    inline=True
                )

                embed.add_field(
                    name="\u200b",
                    value="\u200b",
                    inline=False
                )

                embed.add_field(
                    name="🀄 배팅",
                    value=(
                        f"**{result.bet_okpan:,}개**"
                    ),
                    inline=True
                )

                embed.add_field(
                    name="💸 손실",
                    value=(
                        f"**{result.bet_okpan:,}개**"
                    ),
                    inline=True
                )

                await interaction.response.send_message(
                    embed=embed
                )

                return

        except (ValueError, RuntimeError) as e:

            await interaction.response.send_message(
                str(e),
                ephemeral=True
            )

        except OverflowError:

            await interaction.response.send_message(
                "지급할 옥판 개수가 처리 가능한 범위를 초과했습니다.",
                ephemeral=True
            )

        except Exception as e:

            print(
                f"[숫자 입력 오류] {e}"
            )

            if interaction.response.is_done():

                await interaction.followup.send(
                    "입력한 숫자를 처리하는 중 오류가 발생했습니다.",
                    ephemeral=True
                )

            else:

                await interaction.response.send_message(
                    "입력한 숫자를 처리하는 중 오류가 발생했습니다.",
                    ephemeral=True
                )

    # ============================================
    # /숫자포기
    # ============================================

    @app_commands.command(
        name="숫자포기",
        description="진행 중인 숫자 맞추기 게임을 포기합니다."
    )
    async def give_up(
        self,
        interaction: discord.Interaction
    ):

        discord_id = str(
            interaction.user.id
        )

        try:

            game = (
                await self.number_game_service.give_up(
                    discord_id
                )
            )

            embed = discord.Embed(
                title="🏳️ 숫자 맞추기 포기",
                description=(
                    f"{interaction.user.mention}님이 "
                    "숫자 맞추기 게임을 포기했습니다."
                ),
                color=discord.Color.red()
            )

            embed.add_field(
                name="🎯 정답",
                value=(
                    f"**{game.answer}**"
                ),
                inline=True
            )

            embed.add_field(
                name="📝 사용한 기회",
                value=(
                    f"**{game.attempt_count} / "
                    f"{self.MAX_ATTEMPTS}회**"
                ),
                inline=True
            )

            embed.add_field(
                name="\u200b",
                value="\u200b",
                inline=False
            )

            embed.add_field(
                name="🀄 배팅",
                value=(
                    f"**{game.bet_okpan:,}개**"
                ),
                inline=True
            )

            embed.add_field(
                name="💸 손실",
                value=(
                    f"**{game.bet_okpan:,}개**"
                ),
                inline=True
            )

            await interaction.response.send_message(
                embed=embed
            )

        except RuntimeError as e:

            await interaction.response.send_message(
                str(e),
                ephemeral=True
            )

        except Exception as e:

            print(
                f"[숫자포기 오류] {e}"
            )

            if interaction.response.is_done():

                await interaction.followup.send(
                    "게임 포기 기록을 저장하는 중 오류가 발생했습니다.",
                    ephemeral=True
                )

            else:

                await interaction.response.send_message(
                    "게임 포기 기록을 저장하는 중 오류가 발생했습니다.",
                    ephemeral=True
                )


# ============================================
# Cog 등록
# ============================================

async def setup(
    bot: commands.Bot
):
    await bot.add_cog(
        NumberGameCommand(bot)
    )