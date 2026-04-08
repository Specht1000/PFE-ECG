from pathlib import Path
from typing import List

import pandas as pd

from src.config import (
    CSV_DIR,
    WINDOWS_DIR,
    WINDOW_SIZE_SAMPLES,
    ensure_directories,
)
from src.utils.signal_utils import choose_best_signal_column


def create_windows_from_csv(record_name: str, signal_column: str = None) -> List[Path]:
    ensure_directories()

    input_file = CSV_DIR / f"{record_name}.csv"
    if not input_file.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_file}")

    df = pd.read_csv(input_file)

    signal_columns = [c for c in df.columns if c not in ["sample_index", "time_s"]]

    if signal_column is None:
        signal_column = choose_best_signal_column(signal_columns)

    if signal_column not in df.columns:
        raise ValueError(
            f"Signal column '{signal_column}' not found. Available columns: {list(df.columns)}"
        )

    output_paths = []
    num_samples = len(df)
    window_index = 0

    for start in range(0, num_samples, WINDOW_SIZE_SAMPLES):
        end = start + WINDOW_SIZE_SAMPLES
        window_df = df.iloc[start:end].copy()

        if len(window_df) < WINDOW_SIZE_SAMPLES:
            break

        output_file = WINDOWS_DIR / f"{record_name}_window_{window_index:04d}.csv"
        window_df.to_csv(output_file, index=False)
        output_paths.append(output_file)

        window_index += 1

    print(f"[INFO] Chosen signal column for {record_name}: {signal_column}")
    print(f"[INFO] Created {len(output_paths)} windows for record {record_name}.")
    return output_paths


if __name__ == "__main__":
    files = create_windows_from_csv("100")
    print(files[:3])