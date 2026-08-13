"""
문 단위 금액을 보기 좋은 문자열로 변환하는 유틸리티.
"""


def format_money(money: int) -> str:
    """
    문 단위 금액을 포맷팅한다.

    예)
        1000 -> "1,000문"
    """

    return f"{money:,}문"