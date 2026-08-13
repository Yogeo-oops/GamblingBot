from dataclasses import dataclass


@dataclass(frozen=True)
class OkpanWallet:
    """
    유저의 돈과 등급별 옥판 보유량.

    등급별 수량은 시스템 내부에서만 사용하며,
    일반 유저에게는 전체 옥판 개수만 공개한다.
    """

    # 보유 금액
    money: int

    # 내부 등급별 옥판
    grade1: int
    grade2: int
    grade3: int

    def get_total_okpan(self) -> int:
        """유저에게 공개할 전체 옥판 개수"""
        return self.grade1 + self.grade2 + self.grade3

    def get_okpan_amount(self, grade: int) -> int:
        """
        시스템 내부 또는 운영진 기능에서
        특정 등급의 옥판 개수를 조회한다.
        """

        match grade:
            case 1:
                return self.grade1

            case 2:
                return self.grade2

            case 3:
                return self.grade3

            case _:
                raise ValueError(
                    "옥판 등급은 1등급부터 3등급까지만 가능합니다."
                )