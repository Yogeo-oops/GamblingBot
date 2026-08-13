from dataclasses import dataclass
from enum import Enum


class NumberGuessStatus(Enum):
    TOO_LOW = "TOO_LOW"
    TOO_HIGH = "TOO_HIGH"
    CORRECT = "CORRECT"
    FAILED = "FAILED"


@dataclass(frozen=True)
class NumberGuessResult:
    status: NumberGuessStatus
    attempt_count: int
    answer: int
    payout_okpan: int
    okpan_after: int
    bet_okpan: int