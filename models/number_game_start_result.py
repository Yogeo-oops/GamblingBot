from dataclasses import dataclass


@dataclass(frozen=True)
class NumberGameStartResult:
    # 배팅한 옥판 개수
    bet_okpan: int

    # 배팅 후 남은 전체 옥판 개수
    okpan_after: int