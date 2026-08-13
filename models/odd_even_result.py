from dataclasses import dataclass


@dataclass(frozen=True)
class OddEvenResult:
    # 봇이 선택한 결과 ("홀" 또는 "짝")
    bot_choice: str

    # 승리 여부
    win: bool

    # 게임 결과로 지급된 전체 옥판 개수
    payout_okpan: int

    # 게임 종료 후 보유한 전체 옥판 개수
    okpan_after: int