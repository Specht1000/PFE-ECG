from typing import List

from src.config import PREFERRED_SIGNAL_COLUMNS


def choose_best_signal_column(signal_names: List[str]) -> str:
    """
    Choose the best ECG signal column available in a record.
    Priority:
    MLII -> V5 -> V1 -> V2 -> first available signal
    """
    for preferred in PREFERRED_SIGNAL_COLUMNS:
        if preferred in signal_names:
            return preferred

    if not signal_names:
        raise ValueError("No signal columns available")

    return signal_names[0]