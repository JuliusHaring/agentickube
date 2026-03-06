from logic.strategies.sequence import run_sequence
from logic.strategies.team import run_team

STRATEGY_MAP = {
    "sequence": run_sequence,
    "team": run_team,
}

__all__ = ["STRATEGY_MAP", "run_sequence", "run_team"]
