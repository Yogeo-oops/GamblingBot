from database import Database


class WalletService:
    """
    지갑과 관련된 SQLite DB 작업을 담당한다.
    """

    # ============================================
    # 유저 생성 / 닉네임 갱신
    # ============================================

    async def create_or_update_user(
        self,
        discord_id: str,
        username: str
    ) -> None:

        conn = await Database.get_connection()

        try:

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

            await conn.commit()

        finally:

            await conn.close()

    # ============================================
    # 현재 소지금 조회
    # ============================================

    async def get_money(
        self,
        discord_id: str
    ) -> int:

        conn = await Database.get_connection()

        try:

            cursor = await conn.execute(
                """
                SELECT money
                FROM users
                WHERE discord_id = ?
                """,
                (
                    discord_id,
                )
            )

            row = await cursor.fetchone()

            await cursor.close()

            if row is None:
                return 0

            return int(
                row["money"]
            )

        finally:

            await conn.close()

    # ============================================
    # 돈 지급
    # ============================================

    async def add_money(
        self,
        discord_id: str,
        username: str,
        amount: int
    ) -> int:

        if amount <= 0:
            raise ValueError(
                "지급 금액은 1문 이상이어야 합니다."
            )

        conn = await Database.get_connection()

        try:

            # SQLite에서 쓰기 트랜잭션 시작
            await conn.execute(
                "BEGIN IMMEDIATE"
            )

            # 유저가 없으면 생성,
            # 있으면 닉네임 갱신
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

            # 돈 지급
            cursor = await conn.execute(
                """
                UPDATE users
                SET money = money + ?
                WHERE discord_id = ?
                """,
                (
                    amount,
                    discord_id
                )
            )

            if cursor.rowcount != 1:
                await cursor.close()

                raise RuntimeError(
                    "돈을 지급하지 못했습니다."
                )

            await cursor.close()

            # 변경 후 잔액 조회
            cursor = await conn.execute(
                """
                SELECT money
                FROM users
                WHERE discord_id = ?
                """,
                (
                    discord_id,
                )
            )

            row = await cursor.fetchone()

            await cursor.close()

            if row is None:
                raise RuntimeError(
                    "유저의 지갑 정보를 찾을 수 없습니다."
                )

            new_balance = int(
                row["money"]
            )

            await conn.commit()

            return new_balance

        except Exception:

            await conn.rollback()
            raise

        finally:

            await conn.close()

    # ============================================
    # 돈 차감
    # ============================================

    async def remove_money(
        self,
        discord_id: str,
        username: str,
        amount: int
    ) -> bool:

        if amount <= 0:
            raise ValueError(
                "차감 금액은 1문 이상이어야 합니다."
            )

        conn = await Database.get_connection()

        try:

            await conn.execute(
                "BEGIN IMMEDIATE"
            )

            # 유저가 없으면 생성,
            # 있으면 닉네임 갱신
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

            # 잔액이 충분할 때만 차감
            cursor = await conn.execute(
                """
                UPDATE users
                SET money = money - ?
                WHERE discord_id = ?
                  AND money >= ?
                """,
                (
                    amount,
                    discord_id,
                    amount
                )
            )

            success = (
                cursor.rowcount == 1
            )

            await cursor.close()

            await conn.commit()

            return success

        except Exception:

            await conn.rollback()
            raise

        finally:

            await conn.close()