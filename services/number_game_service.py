import asyncio
import random

from database import Database

from models.number_game import NumberGame
from models.number_game_start_result import NumberGameStartResult
from models.number_guess_result import (
    NumberGuessResult,
    NumberGuessStatus,
)

from services.gamble_stats_service import GambleStatsService
from services.okpan_gamble_service import OkpanGambleService


class NumberGameService:
    """
    숫자 맞추기 게임의 시작, 숫자 입력, 포기를 처리한다.

    게임 배팅과 보상은 모두 옥판을 기준으로 처리한다.

    SQLite 기반으로 동작한다.
    """

    MIN_NUMBER = 1
    MAX_NUMBER = 100
    MAX_ATTEMPTS = 7

    def __init__(
        self
    ):

        self.okpan_gamble_service = (
            OkpanGambleService()
        )

        self.gamble_stats_service = (
            GambleStatsService()
        )

        # ========================================
        # 진행 중인 게임
        # ========================================
        #
        # {
        #     discord_id: NumberGame(...)
        # }

        self.active_games: dict[
            str,
            NumberGame
        ] = {}

        # 동시에 숫자 입력이 들어와
        # 게임 상태가 꼬이지 않도록 보호한다.
        self._lock = asyncio.Lock()

    # ============================================
    # 게임 시작
    # ============================================

    async def start_game(
        self,
        discord_id: str,
        username: str,
        bet_okpan: int
    ) -> NumberGameStartResult:

        if bet_okpan <= 0:

            raise ValueError(
                "배팅할 옥판은 1개 이상이어야 합니다."
            )

        async with self._lock:

            if (
                discord_id
                in self.active_games
            ):

                raise RuntimeError(
                    "이미 숫자 맞추기 게임을 진행 중입니다."
                )

            conn = (
                await Database.get_connection()
            )

            try:

                # SQLite 쓰기 트랜잭션 시작
                await conn.execute(
                    "BEGIN IMMEDIATE"
                )

                # =================================
                # 유저 생성 / 닉네임 갱신
                # =================================

                await self._create_or_update_user(
                    conn,
                    discord_id,
                    username
                )

                # =================================
                # 배팅 옥판 무작위 차감
                # =================================

                await (
                    self.okpan_gamble_service
                    .deduct_random_okpan(
                        conn,
                        discord_id,
                        bet_okpan
                    )
                )

                # =================================
                # 전적 시작 기록
                # =================================

                await (
                    self.gamble_stats_service
                    .record_game_start(
                        conn,
                        discord_id,
                        bet_okpan
                    )
                )

                # =================================
                # 배팅 후 보유 옥판
                # =================================

                okpan_after = (
                    await self.okpan_gamble_service
                    .get_total_okpan(
                        conn,
                        discord_id
                    )
                )

                await conn.commit()

            except Exception:

                await conn.rollback()
                raise

            finally:

                await conn.close()

            # ====================================
            # 정답 생성
            # ====================================

            answer = random.randint(
                self.MIN_NUMBER,
                self.MAX_NUMBER
            )

            self.active_games[
                discord_id
            ] = NumberGame(
                answer=answer,
                bet_okpan=bet_okpan
            )

            return NumberGameStartResult(
                bet_okpan=bet_okpan,
                okpan_after=okpan_after
            )

    # ============================================
    # 숫자 입력
    # ============================================

    async def guess(
        self,
        discord_id: str,
        guessed_number: int
    ) -> NumberGuessResult:

        if (
            guessed_number
            < self.MIN_NUMBER
            or guessed_number
            > self.MAX_NUMBER
        ):

            raise ValueError(
                "숫자는 1부터 100 사이로 입력해야 합니다."
            )

        async with self._lock:

            game = (
                self.active_games.get(
                    discord_id
                )
            )

            if game is None:

                raise RuntimeError(
                    "진행 중인 숫자 맞추기 게임이 없습니다."
                )

            game.increase_attempt_count()

            attempt_count = (
                game.attempt_count
            )

            answer = (
                game.answer
            )

            # ====================================
            # 정답
            # ====================================

            if (
                guessed_number
                == answer
            ):

                payout_okpan = (
                    self._calculate_payout(
                        game.bet_okpan,
                        attempt_count
                    )
                )

                okpan_after = (
                    await self
                    ._reward_okpan_and_record_result(
                        discord_id,
                        payout_okpan
                    )
                )

                # DB 저장이 정상적으로 끝난 뒤
                # 게임 상태 삭제
                self.active_games.pop(
                    discord_id,
                    None
                )

                return NumberGuessResult(
                    status=NumberGuessStatus.CORRECT,
                    attempt_count=attempt_count,
                    answer=answer,
                    payout_okpan=payout_okpan,
                    okpan_after=okpan_after,
                    bet_okpan=game.bet_okpan
                )

            # ====================================
            # 7회 모두 실패
            # ====================================

            if (
                attempt_count
                >= self.MAX_ATTEMPTS
            ):

                okpan_after = (
                    await self
                    ._record_failure_and_get_okpan(
                        discord_id
                    )
                )

                self.active_games.pop(
                    discord_id,
                    None
                )

                return NumberGuessResult(
                    status=NumberGuessStatus.FAILED,
                    attempt_count=attempt_count,
                    answer=answer,
                    payout_okpan=0,
                    okpan_after=okpan_after,
                    bet_okpan=game.bet_okpan
                )

            # ====================================
            # 아직 기회가 남아 있음
            # ====================================

            if (
                guessed_number
                < answer
            ):

                status = (
                    NumberGuessStatus.TOO_LOW
                )

            else:

                status = (
                    NumberGuessStatus.TOO_HIGH
                )

            current_okpan = (
                await self._get_total_okpan(
                    discord_id
                )
            )

            return NumberGuessResult(
                status=status,
                attempt_count=attempt_count,
                answer=answer,
                payout_okpan=0,
                okpan_after=current_okpan,
                bet_okpan=game.bet_okpan
            )

    # ============================================
    # 게임 포기
    # ============================================

    async def give_up(
        self,
        discord_id: str
    ) -> NumberGame:

        async with self._lock:

            game = (
                self.active_games.get(
                    discord_id
                )
            )

            if game is None:

                raise RuntimeError(
                    "진행 중인 숫자 맞추기 게임이 없습니다."
                )

            # 포기는 패배로 기록
            await (
                self.gamble_stats_service
                .record_game_result_separate(
                    discord_id,
                    False,
                    0
                )
            )

            self.active_games.pop(
                discord_id,
                None
            )

            return game

    # ============================================
    # 진행 중인 게임 확인
    # ============================================

    def has_active_game(
        self,
        discord_id: str
    ) -> bool:

        return (
            discord_id
            in self.active_games
        )

    # ============================================
    # 지급량 계산
    # ============================================

    def _calculate_payout(
        self,
        bet_okpan: int,
        attempt_count: int
    ) -> int:
        """
        성공 횟수에 따른 지급 옥판.

        1회: 20배
        2회: 10배
        3회: 5배
        4회: 3배
        5회: 2배
        6회: 1배
        7회: 0.5배
        """

        multipliers = {
            1: (20, 1),
            2: (10, 1),
            3: (5, 1),
            4: (3, 1),
            5: (2, 1),
            6: (1, 1),
            7: (1, 2),
        }

        multiplier = (
            multipliers.get(
                attempt_count
            )
        )

        if multiplier is None:

            raise ValueError(
                "잘못된 시도 횟수입니다."
            )

        numerator, denominator = (
            multiplier
        )

        return (
            bet_okpan
            * numerator
            // denominator
        )

    # ============================================
    # 정답 성공 처리
    # ============================================

    async def _reward_okpan_and_record_result(
        self,
        discord_id: str,
        payout_okpan: int
    ) -> int:

        conn = (
            await Database.get_connection()
        )

        try:

            await conn.execute(
                "BEGIN IMMEDIATE"
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
            # 승리 전적 기록
            # ====================================

            await (
                self.gamble_stats_service
                .record_game_result(
                    conn,
                    discord_id,
                    True,
                    payout_okpan
                )
            )

            # ====================================
            # 현재 전체 옥판
            # ====================================

            okpan_after = (
                await self.okpan_gamble_service
                .get_total_okpan(
                    conn,
                    discord_id
                )
            )

            await conn.commit()

            return okpan_after

        except Exception:

            await conn.rollback()
            raise

        finally:

            await conn.close()

    # ============================================
    # 7회 실패 처리
    # ============================================

    async def _record_failure_and_get_okpan(
        self,
        discord_id: str
    ) -> int:

        conn = (
            await Database.get_connection()
        )

        try:

            await conn.execute(
                "BEGIN IMMEDIATE"
            )

            # 패배 전적 기록
            await (
                self.gamble_stats_service
                .record_game_result(
                    conn,
                    discord_id,
                    False,
                    0
                )
            )

            okpan_after = (
                await self.okpan_gamble_service
                .get_total_okpan(
                    conn,
                    discord_id
                )
            )

            await conn.commit()

            return okpan_after

        except Exception:

            await conn.rollback()
            raise

        finally:

            await conn.close()

    # ============================================
    # 현재 전체 옥판 조회
    # ============================================

    async def _get_total_okpan(
        self,
        discord_id: str
    ) -> int:

        conn = (
            await Database.get_connection()
        )

        try:

            return (
                await self.okpan_gamble_service
                .get_total_okpan(
                    conn,
                    discord_id
                )
            )

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