from database import Database


class WalletService:
    """
    지갑과 관련된 DB 작업을 담당한다.
    """

    # ============================================
    # 유저 생성 / 닉네임 갱신
    # ============================================

    async def create_or_update_user(
        self,
        discord_id: str,
        username: str
    ) -> None:
        """
        유저가 DB에 없으면 새로 생성하고,
        이미 있으면 닉네임만 최신 상태로 갱신한다.
        """

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

        conn = await Database.get_connection()

        try:
            cursor = await conn.cursor()

            try:
                await cursor.execute(
                    sql,
                    (
                        discord_id,
                        username
                    )
                )

                await conn.commit()

            finally:
                await cursor.close()

        finally:
            await conn.close()

    # ============================================
    # 현재 소지금 조회
    # ============================================

    async def get_money(
        self,
        discord_id: str
    ) -> int:
        """
        유저의 현재 소지금을 반환한다.

        유저가 DB에 존재하지 않으면 0을 반환한다.
        """

        sql = """
            SELECT money
            FROM users
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
                    return row["money"]

            finally:
                await cursor.close()

        finally:
            await conn.close()

        return 0

    # ============================================
    # 돈 지급
    # ============================================

    async def add_money(
        self,
        discord_id: str,
        username: str,
        amount: int
    ) -> int:
        """
        유저에게 돈을 지급한다.

        지급 후 변경된 소지금을 반환한다.
        """

        if amount <= 0:
            raise ValueError(
                "지급 금액은 1문 이상이어야 합니다."
            )

        await self.create_or_update_user(
            discord_id,
            username
        )

        sql = """
            UPDATE users
            SET money = money + %s
            WHERE discord_id = %s
        """

        conn = await Database.get_connection()

        try:
            cursor = await conn.cursor()

            try:
                await cursor.execute(
                    sql,
                    (
                        amount,
                        discord_id
                    )
                )

                if cursor.rowcount != 1:
                    raise RuntimeError(
                        "돈을 지급할 유저를 찾을 수 없습니다."
                    )

                await conn.commit()

            finally:
                await cursor.close()

        finally:
            await conn.close()

        return await self.get_money(
            discord_id
        )

    # ============================================
    # 돈 차감
    # ============================================

    async def remove_money(
        self,
        discord_id: str,
        username: str,
        amount: int
    ) -> bool:
        """
        유저의 돈을 차감한다.

        잔액이 충분하면 차감 후 True를 반환하고,
        잔액이 부족하면 돈을 건드리지 않고 False를 반환한다.
        """

        if amount <= 0:
            raise ValueError(
                "차감 금액은 1문 이상이어야 합니다."
            )

        await self.create_or_update_user(
            discord_id,
            username
        )

        sql = """
            UPDATE users
            SET money = money - %s
            WHERE discord_id = %s
              AND money >= %s
        """

        conn = await Database.get_connection()

        try:
            cursor = await conn.cursor()

            try:
                await cursor.execute(
                    sql,
                    (
                        amount,
                        discord_id,
                        amount
                    )
                )

                changed_rows = cursor.rowcount

                await conn.commit()

                # 1개 행 수정 -> 차감 성공
                # 0개 행 수정 -> 잔액 부족
                return changed_rows == 1

            finally:
                await cursor.close()

        finally:
            await conn.close()