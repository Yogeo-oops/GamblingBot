from database import Database
from models.gamble_stats import GambleStats


class GambleStatsService:
    """
    도박 전적의 생성, 누적, 조회를 담당한다.

    SQLite 기반으로 동작한다.
    """

    # ============================================
    # 게임 시작 기록
    # ============================================

    async def record_game_start(
        self,
        conn,
        discord_id: str,
        bet_amount: int
    ) -> None:

        if bet_amount <= 0:

            raise ValueError(
                "배팅 옥판은 1개 이상이어야 합니다."
            )

        # 전적 행이 없으면 생성
        await self._create_stats_if_missing(
            conn,
            discord_id
        )

        cursor = await conn.execute(
            """
            UPDATE gamble_stats
            SET total_games = total_games + 1,
                total_bet = total_bet + ?
            WHERE discord_id = ?
            """,
            (
                bet_amount,
                discord_id
            )
        )

        if cursor.rowcount != 1:

            await cursor.close()

            raise RuntimeError(
                "도박 시작 전적을 저장하지 못했습니다."
            )

        await cursor.close()

    # ============================================
    # 게임 결과 기록
    # ============================================

    async def record_game_result(
        self,
        conn,
        discord_id: str,
        win: bool,
        payout: int
    ) -> None:

        if payout < 0:

            raise ValueError(
                "지급 옥판은 0개 이상이어야 합니다."
            )

        # 전적 행이 없으면 생성
        await self._create_stats_if_missing(
            conn,
            discord_id
        )

        # ========================================
        # 승 / 패 컬럼 결정
        # ========================================

        result_column = (
            "total_wins"
            if win
            else "total_losses"
        )

        # result_column은 코드 내부에서만
        # 허용된 두 컬럼 중 하나로 결정된다.
        cursor = await conn.execute(
            f"""
            UPDATE gamble_stats
            SET {result_column}
                    = {result_column} + 1,
                total_payout
                    = total_payout + ?,
                max_payout
                    = MAX(max_payout, ?)
            WHERE discord_id = ?
            """,
            (
                payout,
                payout,
                discord_id
            )
        )

        if cursor.rowcount != 1:

            await cursor.close()

            raise RuntimeError(
                "도박 결과 전적을 저장하지 못했습니다."
            )

        await cursor.close()

    # ============================================
    # 별도 Connection으로 결과 기록
    # ============================================
    #
    # 숫자 맞추기 포기처럼
    # 기존 트랜잭션 밖에서 결과만 저장할 때 사용한다.

    async def record_game_result_separate(
        self,
        discord_id: str,
        win: bool,
        payout: int
    ) -> None:

        conn = await Database.get_connection()

        try:

            await conn.execute(
                "BEGIN IMMEDIATE"
            )

            await self.record_game_result(
                conn,
                discord_id,
                win,
                payout
            )

            await conn.commit()

        except Exception:

            await conn.rollback()
            raise

        finally:

            await conn.close()

    # ============================================
    # 전적 조회
    # ============================================

    async def get_stats(
        self,
        discord_id: str
    ) -> GambleStats:

        conn = await Database.get_connection()

        try:

            cursor = await conn.execute(
                """
                SELECT
                    total_games,
                    total_wins,
                    total_losses,
                    total_bet,
                    total_payout,
                    max_payout
                FROM gamble_stats
                WHERE discord_id = ?
                """,
                (
                    discord_id,
                )
            )

            row = await cursor.fetchone()

            await cursor.close()

            if row is not None:

                return GambleStats(
                    total_games=int(
                        row["total_games"]
                    ),
                    total_wins=int(
                        row["total_wins"]
                    ),
                    total_losses=int(
                        row["total_losses"]
                    ),
                    total_bet=int(
                        row["total_bet"]
                    ),
                    total_payout=int(
                        row["total_payout"]
                    ),
                    max_payout=int(
                        row["max_payout"]
                    )
                )

            # 전적이 없으면 전부 0
            return GambleStats(
                total_games=0,
                total_wins=0,
                total_losses=0,
                total_bet=0,
                total_payout=0,
                max_payout=0
            )

        finally:

            await conn.close()

    # ============================================
    # 전적 행 생성
    # ============================================

    async def _create_stats_if_missing(
        self,
        conn,
        discord_id: str
    ) -> None:

        await conn.execute(
            """
            INSERT OR IGNORE
            INTO gamble_stats (
                discord_id
            )
            VALUES (?)
            """,
            (
                discord_id,
            )
        )