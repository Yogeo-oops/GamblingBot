import random

from database import Database

from models.odd_even_result import OddEvenResult
from models.yut_game_result import YutGameResult
from models.yut_outcome import YutOutcome

from services.gamble_stats_service import GambleStatsService
from services.okpan_gamble_service import OkpanGambleService


class GambleService:
    """
    홀짝과 윷놀이의 게임 처리 및 결과 계산을 담당한다.

    두 게임 모두 돈이 아닌 옥판을 사용한다.

    SQLite 기반으로 동작한다.
    """

    def __init__(self):

        # 도박 전적 저장
        self.gamble_stats_service = (
            GambleStatsService()
        )

        # 옥판 차감 / 지급
        self.okpan_gamble_service = (
            OkpanGambleService()
        )

    # ============================================
    # 홀짝
    # ============================================

    async def play_odd_even(
        self,
        discord_id: str,
        username: str,
        user_choice: str,
        bet_okpan: int
    ) -> OddEvenResult:

        if bet_okpan <= 0:

            raise ValueError(
                "배팅할 옥판은 1개 이상이어야 합니다."
            )

        if user_choice not in (
            "홀",
            "짝"
        ):

            raise ValueError(
                "홀 또는 짝만 선택할 수 있습니다."
            )

        conn = await Database.get_connection()

        try:

            # SQLite 쓰기 트랜잭션 시작
            await conn.execute(
                "BEGIN IMMEDIATE"
            )

            # ====================================
            # 유저 생성 / 닉네임 갱신
            # ====================================

            await self._create_or_update_user(
                conn,
                discord_id,
                username
            )

            # ====================================
            # 배팅 옥판 무작위 차감
            # ====================================

            await (
                self.okpan_gamble_service
                .deduct_random_okpan(
                    conn,
                    discord_id,
                    bet_okpan
                )
            )

            # ====================================
            # 게임 시작 전적 기록
            # ====================================

            await (
                self.gamble_stats_service
                .record_game_start(
                    conn,
                    discord_id,
                    bet_okpan
                )
            )

            # ====================================
            # 홀 / 짝 결정
            # ====================================

            bot_choice = (
                "홀"
                if random.choice(
                    [True, False]
                )
                else "짝"
            )

            win = (
                user_choice
                == bot_choice
            )

            # ====================================
            # 지급량 계산
            # ====================================
            #
            # 승리 시 배팅의 2배 지급

            payout_okpan = (
                bet_okpan * 2
                if win
                else 0
            )

            # ====================================
            # 보상 옥판 지급
            # ====================================

            await (
                self.okpan_gamble_service
                .add_random_reward_okpan(
                    conn,
                    discord_id,
                    payout_okpan
                )
            )

            # ====================================
            # 결과 전적 기록
            # ====================================

            await (
                self.gamble_stats_service
                .record_game_result(
                    conn,
                    discord_id,
                    win,
                    payout_okpan
                )
            )

            # ====================================
            # 게임 종료 후 전체 옥판
            # ====================================

            okpan_after = (
                await self.okpan_gamble_service
                .get_total_okpan(
                    conn,
                    discord_id
                )
            )

            await conn.commit()

            return OddEvenResult(
                bot_choice=bot_choice,
                win=win,
                payout_okpan=payout_okpan,
                okpan_after=okpan_after
            )

        except Exception:

            await conn.rollback()
            raise

        finally:

            await conn.close()

    # ============================================
    # 윷놀이
    # ============================================

    async def play_yut(
        self,
        discord_id: str,
        username: str,
        bet_okpan: int
    ) -> YutGameResult:

        if bet_okpan <= 0:

            raise ValueError(
                "배팅할 옥판은 1개 이상이어야 합니다."
            )

        conn = await Database.get_connection()

        try:

            await conn.execute(
                "BEGIN IMMEDIATE"
            )

            # ====================================
            # 유저 생성 / 닉네임 갱신
            # ====================================

            await self._create_or_update_user(
                conn,
                discord_id,
                username
            )

            # ====================================
            # 배팅 옥판 무작위 차감
            # ====================================

            await (
                self.okpan_gamble_service
                .deduct_random_okpan(
                    conn,
                    discord_id,
                    bet_okpan
                )
            )

            # ====================================
            # 게임 시작 전적 기록
            # ====================================

            await (
                self.gamble_stats_service
                .record_game_start(
                    conn,
                    discord_id,
                    bet_okpan
                )
            )

            # ====================================
            # 윷 결과 추첨
            # ====================================

            outcome = (
                self._draw_yut_outcome()
            )

            # ====================================
            # 지급량 계산
            # ====================================

            payout_okpan = (
                outcome.calculate_payout(
                    bet_okpan
                )
            )

            # ====================================
            # 보상 옥판 지급
            # ====================================

            await (
                self.okpan_gamble_service
                .add_random_reward_okpan(
                    conn,
                    discord_id,
                    payout_okpan
                )
            )

            # ====================================
            # 승패 기준
            # ====================================
            #
            # payout >= bet 이면 승리로 기록
            #
            # 백도 0배
            # 도   0.5배
            # 개   1배
            # 걸 이상 승리

            win = (
                payout_okpan
                >= bet_okpan
            )

            # ====================================
            # 결과 전적 기록
            # ====================================

            await (
                self.gamble_stats_service
                .record_game_result(
                    conn,
                    discord_id,
                    win,
                    payout_okpan
                )
            )

            # ====================================
            # 게임 종료 후 전체 옥판
            # ====================================

            okpan_after = (
                await self.okpan_gamble_service
                .get_total_okpan(
                    conn,
                    discord_id
                )
            )

            await conn.commit()

            return YutGameResult(
                outcome=outcome,
                payout_okpan=payout_okpan,
                okpan_after=okpan_after
            )

        except Exception:

            await conn.rollback()
            raise

        finally:

            await conn.close()

    # ============================================
    # 유저 생성 / 닉네임 갱신
    # ============================================

    async def _create_or_update_user(
        self,
        conn,
        discord_id: str,
        username: str
    ) -> None:

        await conn.execute(
            """
            INSERT INTO users (
                discord_id,
                username,
                money
            )
            VALUES (?, ?, 0)

            ON CONFLICT(discord_id)
            DO UPDATE SET
                username = excluded.username
            """,
            (
                discord_id,
                username
            )
        )

    # ============================================
    # 윷 결과 추첨
    # ============================================

    def _draw_yut_outcome(
        self
    ) -> YutOutcome:

        outcomes = list(
            YutOutcome
        )

        total_weight = sum(
            outcome.weight
            for outcome in outcomes
        )

        random_number = (
            random.randint(
                1,
                total_weight
            )
        )

        accumulated_weight = 0

        for outcome in outcomes:

            accumulated_weight += (
                outcome.weight
            )

            if (
                random_number
                <= accumulated_weight
            ):

                return outcome

        raise RuntimeError(
            "윷놀이 결과를 결정하지 못했습니다."
        )