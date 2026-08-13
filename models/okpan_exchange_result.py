from dataclasses import dataclass

from models.okpan_wallet import OkpanWallet


@dataclass(frozen=True)
class OkpanExchangeResult:
    # 내부 시스템 확인용
    exchanged_grade1: int
    exchanged_grade2: int
    exchanged_grade3: int

    # 환전으로 지급된 금액
    received_money: int

    # 환전 후 지갑 상태
    wallet_after: OkpanWallet

    def get_exchanged_total(self) -> int:
        """환전한 전체 옥판 개수"""
        return (
            self.exchanged_grade1
            + self.exchanged_grade2
            + self.exchanged_grade3
        )