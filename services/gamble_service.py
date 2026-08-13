import random

from models.odd_even_result import OddEvenResult
from models.yut_game_result import YutGameResult
from models.yut_outcome import YutOutcome

from services.gamble_stats_service import GambleStatsService
from services.okpan_gamble_service import OkpanGambleService

from database import Database


class GambleService:
    """
    홀짝과 윷놀이의 게임 처리 및 결과 계산을 담당한다.

    두 게임 모두 돈이 아닌 옥판을 사용한다.
    """

    def __init__(self):
        # 도박 전적 저장용 서비스
        self.gamble_stats_service = GambleStatsService()

        # 도박용 옥판 차감 및 지급 서비스
        self.okpan_gamble_service = OkpanGambleService()

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

        if user_choice not in ("홀", "짝"):
            raise ValueError(
                "홀 또는 짝만 선택할 수 있습니다."
            )

        conn = await Database.get_connection()

        try:
            # 트랜잭션 시작
            await conn.start_transaction()

            # 유저가 없으면 생성하고,
            # 이미 있으면 닉네임 갱신
            await self._create_or_update_user(
                conn,
                discord_id,
                username
            )

            # 실제 보유 옥판 중 배팅 수량만큼 무작위 차감
            await self.okpan_gamble_service.deduct_random_okpan(
                conn,
                discord_id,
                bet_okpan
            )

            # 전체 게임 횟수와 총 배팅 옥판 기록
            await self.gamble_stats_service.record_game_start(
                conn,
                discord_id,
                bet_okpan
            )

            # 홀 / 짝 랜덤 결정
            bot_choice = random.choice(
                ("홀", "짝")
            )

            win = user_choice == bot_choice

            # 승리 시 배팅 옥판의 2배 지급
            payout_okpan = (
                bet_okpan * 2
                if win
                else 0
            )

            # 지급되는 옥판은 각각 내부 등급 추첨
            await self.okpan_gamble_service.add_random_reward_okpan(
                conn,
                discord_id,
                payout_okpan
            )

            # 승패 및 지급 옥판 기록
            await self.gamble_stats_service.record_game_result(
                conn,
                discord_id,
                win,
                payout_okpan
            )

            # 게임 종료 후 총 옥판 개수
            okpan_after = (
                await self.okpan_gamble_service.get_total_okpan(
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
            # 트랜잭션 시작
            await conn.start_transaction()

            # 유저가 없으면 생성하고,
            # 이미 있으면 닉네임 갱신
            await self._create_or_update_user(
                conn,
                discord_id,
                username
            )

            # 실제 보유 옥판 중 배팅 수량만큼 무작위 차감
            await self.okpan_gamble_service.deduct_random_okpan(
                conn,
                discord_id,
                bet_okpan
            )

            # 전체 게임 수와 총 배팅 옥판 기록
            await self.gamble_stats_service.record_game_start(
                conn,
                discord_id,
                bet_okpan
            )

            # 가중치에 따라 윷 결과 결정
            outcome = self._draw_yut_outcome()

            # 배율에 따른 지급 옥판 계산
            payout_okpan = outcome.calculate_payout(
                bet_okpan
            )

            # 지급되는 옥판은 각각 내부 등급 추첨
            await self.okpan_gamble_service.add_random_reward_okpan(
                conn,
                discord_id,
                payout_okpan
            )

            """
            승패 기준

            백도 0배   -> 패배
            도 0.5배   -> 패배
            개 1배     -> 승리
            걸 이상    -> 승리
            """
            win = payout_okpan >= bet_okpan

            # 전적 기록
            await self.gamble_stats_service.record_game_result(
                conn,
                discord_id,
                win,
                payout_okpan
            )

            # 게임 종료 후 총 옥판 개수
            okpan_after = (
                await self.okpan_gamble_service.get_total_okpan(
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

        sql = """
            INSERT INTO users (
                discord_id,
                username,
                money
            )
            VALUES (%s, %s, 0)
            ON DUPLICATE KEY UPDATE
                username = VALUES(username)
        """

        cursor = await conn.cursor()

        try:
            await cursor.execute(
                sql,
                (
                    discord_id,
                    username
                )
            )

        finally:
            await cursor.close()

    # ============================================
    # 윷 결과 추첨
    # ============================================

    def _draw_yut_outcome(self) -> YutOutcome:
        """
        설정된 가중치에 따라 윷 결과를 결정한다.
        """

        total_weight = sum(
            outcome.weight
            for outcome in YutOutcome
        )

        random_number = random.randint(
            1,
            total_weight
        )

        accumulated_weight = 0

        for outcome in YutOutcome:
            accumulated_weight += outcome.weight

            if random_number <= accumulated_weight:
                return outcome

        # 정상적인 가중치라면 여기까지 올 수 없음
        raise RuntimeError(
            "윷놀이 결과를 결정하지 못했습니다."
        )