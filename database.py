import os

import mysql.connector.aio
from dotenv import load_dotenv


# .env 파일의 환경변수를 불러온다.
load_dotenv()


class Database:
    """
    MySQL 연결을 관리한다.

    Java 버전에서는 HikariCP Connection Pool을 사용했지만,
    Python 버전에서는 필요한 시점에 비동기 연결을 생성하고
    사용이 끝나면 각 Service에서 close()한다.
    """

    @staticmethod
    async def get_connection():
        """
        새로운 비동기 MySQL Connection을 생성하여 반환한다.
        """

        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT", "3306")
        database = os.getenv("DB_NAME")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")

        # 필수 설정값 확인
        if not host:
            raise RuntimeError(
                ".env에 DB_HOST 값이 없습니다."
            )

        if not database:
            raise RuntimeError(
                ".env에 DB_NAME 값이 없습니다."
            )

        if not user:
            raise RuntimeError(
                ".env에 DB_USER 값이 없습니다."
            )

        if password is None:
            raise RuntimeError(
                ".env에 DB_PASSWORD 값이 없습니다."
            )

        try:
            port_number = int(port)

        except ValueError as e:
            raise RuntimeError(
                "DB_PORT는 숫자여야 합니다."
            ) from e

        connection = await mysql.connector.aio.connect(
            host=host,
            port=port_number,
            database=database,
            user=user,
            password=password,

            # 트랜잭션을 코드에서 직접 관리한다.
            autocommit=False
        )

        return connection