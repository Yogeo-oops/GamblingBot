from enum import Enum


class YutOutcome(Enum):
    """
    윷놀이 결과와 확률, 지급 배율을 정의한다.
    """

    # (출력 이름, 가중치, 배율 분자, 배율 분모)
    BACK_DO = ("백도", 100, 0, 1)
    DO = ("도", 200, 1, 2)
    GAE = ("개", 300, 1, 1)
    GEOL = ("걸", 200, 2, 1)
    YUT = ("윷", 150, 3, 1)
    MO = ("모", 50, 5, 1)

    def __init__(
        self,
        display_name: str,
        weight: int,
        multiplier_numerator: int,
        multiplier_denominator: int
    ):
        self.display_name = display_name
        self.weight = weight
        self.multiplier_numerator = multiplier_numerator
        self.multiplier_denominator = multiplier_denominator

    def calculate_payout(
        self,
        bet_okpan: int
    ) -> int:
        """
        배팅한 옥판에 배율을 적용하여 지급 옥판을 계산한다.
        """

        return (
            bet_okpan
            * self.multiplier_numerator
            // self.multiplier_denominator
        )

    @property
    def multiplier_text(self) -> str:
        """
        출력용 배율 문자열.
        """

        if self.multiplier_numerator == 0:
            return "0배"

        if (
            self.multiplier_numerator == 1
            and self.multiplier_denominator == 2
        ):
            return "0.5배"

        return f"{self.multiplier_numerator}배"