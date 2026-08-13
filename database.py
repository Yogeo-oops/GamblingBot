from pathlib import Path

import aiosqlite


class Database:
    """
    SQLite 데이터베이스 연결과 초기화를 담당한다.

    별도의 DB 서버 없이 프로젝트 내부의
    gambling.db 파일에 모든 데이터를 저장한다.
    """

    # ============================================
    # DB 파일 위치
    # ============================================
    #
    # database.py와 같은 폴더에
    # gambling.db 파일이 생성된다.

    DB_PATH = (
        Path(__file__).resolve().parent
        / "gambling.db"
    )

    # ============================================
    # 데이터베이스 초기화
    # ============================================

    @classmethod
    async def init(cls) -> None:
        """
        프로그램 시작 시 한 번 실행한다.

        gambling.db가 없으면 자동으로 생성하고,
        필요한 테이블도 자동으로 생성한다.
        """

        async with aiosqlite.connect(
            cls.DB_PATH
        ) as conn:

            # 여러 읽기/쓰기 작업이 조금 더 안정적으로
            # 동시에 처리될 수 있도록 WAL 모드 사용
            await conn.execute(
                "PRAGMA journal_mode = WAL"
            )

            await conn.execute(
                "PRAGMA foreign_keys = ON"
            )

            # ====================================
            # users 테이블
            # ====================================

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    discord_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,

                    money INTEGER NOT NULL DEFAULT 0,

                    okpan_grade_1 INTEGER NOT NULL DEFAULT 0,
                    okpan_grade_2 INTEGER NOT NULL DEFAULT 0,
                    okpan_grade_3 INTEGER NOT NULL DEFAULT 0,

                    last_salary_date TEXT DEFAULT NULL
                )
                """
            )

            # ====================================
            # gamble_stats 테이블
            # ====================================

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS gamble_stats (
                    discord_id TEXT PRIMARY KEY,

                    total_games INTEGER NOT NULL DEFAULT 0,
                    total_wins INTEGER NOT NULL DEFAULT 0,
                    total_losses INTEGER NOT NULL DEFAULT 0,

                    total_bet INTEGER NOT NULL DEFAULT 0,
                    total_payout INTEGER NOT NULL DEFAULT 0,
                    max_payout INTEGER NOT NULL DEFAULT 0,

                    FOREIGN KEY (discord_id)
                        REFERENCES users(discord_id)
                        ON DELETE CASCADE
                )
                """
            )

            await conn.commit()

        print("=" * 40)
        print(" SQLite 데이터베이스 준비 완료")
        print(f" DB 위치: {cls.DB_PATH}")
        print("=" * 40)

    # ============================================
    # DB 연결 반환
    # ============================================

    @classmethod
    async def get_connection(
        cls
    ) -> aiosqlite.Connection:
        """
        새로운 SQLite Connection을 반환한다.

        호출한 쪽에서 반드시 close() 해야 한다.
        """

        conn = await aiosqlite.connect(
            cls.DB_PATH,
            timeout=30
        )

        # SELECT 결과를
        # row["money"] 같은 방식으로 사용할 수 있게 함
        conn.row_factory = aiosqlite.Row

        await conn.execute(
            "PRAGMA foreign_keys = ON"
        )

        return conn