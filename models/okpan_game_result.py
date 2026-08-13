from dataclasses import dataclass


@dataclass(frozen=True)
class OkpanGameResult:
    """
    도박으로 지급된 옥판의 내부 등급별 결과.

    등급별 수량은 시스템 내부 처리용이며,
    일반 유저에게는 공개하지 않는다.
    """

    grade1: int
    grade2: int
    grade3: int

    def get_total(self) -> int:
        """유저에게 지급된 전체 옥판 개수"""
        return self.grade1 + self.grade2 + self.grade3