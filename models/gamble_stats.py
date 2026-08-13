from dataclasses import dataclass


@dataclass
class GambleStats:
    total_games: int
    total_wins: int
    total_losses: int

    total_bet: int
    total_payout: int
    max_payout: int

    def get_profit(self) -> int:
        return self.total_payout - self.total_bet

    def get_win_rate(self) -> float:
        if self.total_games == 0:
            return 0.0

        return self.total_wins * 100.0 / self.total_games