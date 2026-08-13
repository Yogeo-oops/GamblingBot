from dataclasses import dataclass

from models.yut_outcome import YutOutcome


@dataclass(frozen=True)
class YutGameResult:
    """
    윷놀이 결과를 담는 객체.

    일반 유저에게는 옥판 등급을 공개하지 않고,
    지급된 총 옥판 개수와 게임 종료 후 총 옥판 개수만 전달한다.
    """

    # 나온 윷 결과
    outcome: YutOutcome

    # 결과에 따라 지급된 옥판 개수
    payout_okpan: int

    # 게임 종료 후 보유 중인 총 옥판 개수
    okpan_after: int