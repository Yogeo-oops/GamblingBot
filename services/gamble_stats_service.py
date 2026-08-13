from database import Database
from models.gamble_stats import GambleStats


class GambleStatsService:
    """
    도박 전적의 생성, 누적, 조회를 담당한다.
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
        """
        게임 시작 시 호출한다.

        전체 게임 횟수를 1 증가시키고,
        총 배팅량에 이번 배팅량을 더한다.

        외부에서 전달받은 Connection을 사용하므로
        옥판 차감 등의 처리와 같은 트랜잭션 안에서 묶을 수 있다.
        """

        if bet_amount <= 0:
            raise ValueError(
                "배팅 옥판은 1개 이상이어야 합니다."
            )

        # 전적 행이 없으면 먼저 생성
        await self._create_stats_if_missing(
            conn,
            discord_id
        )

        sql = """
            UPDATE gamble_stats
            SET total_games = total_games + 1,
                total_bet = total_bet + %s
            WHERE discord_id = %s
        """

        cursor = await conn.cursor()

        try:
            await cursor.execute(
                sql,
                (
                    bet_amount,
                    discord_id
                )
            )

            if cursor.rowcount != 1:
                raise RuntimeError(
                    "도박 시작 전적을 저장하지 못했습니다."
                )

        finally:
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
        """
        게임 종료 시 호출한다.

        승리 또는 패배 횟수를 증가시키고,
        총 지급량과 최고 지급량을 갱신한다.
        """

        if payout < 0:
            raise ValueError(
                "지급 옥판은 0개 이상이어야 합니다."
            )

        # 안전을 위해 전적 행이 없으면 생성
        await self._create_stats_if_missing(
            conn,
            discord_id
        )

        result_column = (
            "total_wins"
            if win
            else "total_losses"
        )

        # result_column은 코드 내부에서만
        # total_wins / total_losses 중 하나로 결정되므로 안전하다.
        sql = f"""
            UPDATE gamble_stats
            SET {result_column} = {result_column} + 1,
                total_payout = total_payout + %s,
                max_payout = GREATEST(max_payout, %s)
            WHERE discord_id = %s
        """

        cursor = await conn.cursor()

        try:
            await cursor.execute(
                sql,
                (
                    payout,
                    payout,
                    discord_id
                )
            )

            if cursor.rowcount != 1:
                raise RuntimeError(
                    "도박 결과 전적을 저장하지 못했습니다."
                )

        finally:
            await cursor.close()

    # ============================================
    # 별도 연결로 게임 결과 기록
    # ============================================

    async def record_game_result_separate(
        self,
        discord_id: str,
        win: bool,
        payout: int
    ) -> None:
        """
        숫자 맞추기처럼
        게임 시작과 종료가 서로 다른 명령어에서 처리되는 경우 사용한다.

        별도의 DB 연결과 트랜잭션을 생성한다.
        """

        conn = await Database.get_connection()

        try:
            await conn.start_transaction()

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
        """
        유저의 도박 전적을 조회한다.

        아직 전적이 없으면
        모든 값이 0인 GambleStats 객체를 반환한다.
        """

        sql = """
            SELECT
                total_games,
                total_wins,
                total_losses,
                total_bet,
                total_payout,
                max_payout
            FROM gamble_stats
            WHERE discord_id = %s
        """

        conn = await Database.get_connection()

        try:
            cursor = await conn.cursor(
                dictionary=True
            )

            try:
                await cursor.execute(
                    sql,
                    (discord_id,)
                )

                row = await cursor.fetchone()

                if row is not None:
                    return GambleStats(
                        total_games=row["total_games"],
                        total_wins=row["total_wins"],
                        total_losses=row["total_losses"],
                        total_bet=row["total_bet"],
                        total_payout=row["total_payout"],
                        max_payout=row["max_payout"]
                    )

            finally:
                await cursor.close()

        finally:
            await conn.close()

        return GambleStats(
            total_games=0,
            total_wins=0,
            total_losses=0,
            total_bet=0,
            total_payout=0,
            max_payout=0
        )

    # ============================================
    # 전적 행 생성
    # ============================================

    async def _create_stats_if_missing(
        self,
        conn,
        discord_id: str
    ) -> None:
        """
        해당 유저의 전적 행이 없으면 생성한다.
        """

        sql = """
            INSERT IGNORE INTO gamble_stats (
                discord_id
            )
            VALUES (%s)
        """

        cursor = await conn.cursor()

        try:
            await cursor.execute(
                sql,
                (discord_id,)
            )

        finally:
            await cursor.close()