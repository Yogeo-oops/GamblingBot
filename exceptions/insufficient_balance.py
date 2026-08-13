class InsufficientBalanceException(Exception):
    """소지금이 부족할 때 발생하는 예외."""

    def __init__(self, message: str = "소지금이 부족합니다."):
        super().__init__(message)