from dataclasses import dataclass


@dataclass
class NumberGame:
    # 봇이 정한 정답
    answer: int

    # 게임 시작 시 배팅한 옥판 개수
    bet_okpan: int

    # 현재까지 시도 횟수
    attempt_count: int = 0

    def increase_attempt_count(self) -> None:
        """숫자를 입력할 때마다 시도 횟수를 1 증가시킨다."""
        self.attempt_count += 1