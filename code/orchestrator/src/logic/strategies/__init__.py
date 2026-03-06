from logic.strategies.sequence import run_sequence
from logic.strategies.council import run_council

STRATEGY_MAP = {
    "sequence": run_sequence,
    "council": run_council,
}

__all__ = ["STRATEGY_MAP", "run_sequence", "run_council"]
