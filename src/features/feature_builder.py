import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from src.config import WINDOWS_DIR, PROCESSED_DIR, CSV_DIR, ensure_directories
from src.utils.signal_utils import choose_best_signal_column


def extract_basic_features(window_df: pd.DataFrame, signal_column: str) -> Dict[str, float]:
    signal = window_df[signal_column].to_numpy()

    features = {
        "mean": float(np.mean(signal)),
        "std": float(np.std(signal)),
        "min": float(np.min(signal)),
        "max": float(np.max(signal)),
        "range": float(np.max(signal) - np.min(signal)),
        "energy": float(np.sum(signal ** 2)),
    }

    return features


def build_feature_table(record_name: str, signal_column: str = None) -> Path:
    ensure_directories()

    meta_file = CSV_DIR / f"{record_name}_meta.json"
    if not meta_file.exists():
        raise FileNotFoundError(f"Metadata file not found: {meta_file}")

    with open(meta_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    signal_names = metadata["signal_names"]
    comments = metadata.get("comments", [])

    if signal_column is None:
        signal_column = choose_best_signal_column(signal_names)

    window_files = sorted(WINDOWS_DIR.glob(f"{record_name}_window_*.csv"))
    if not window_files:
        raise FileNotFoundError(f"No windows found for record {record_name} in {WINDOWS_DIR}")

    rows: List[Dict[str, float]] = []

    for window_file in window_files:
        window_df = pd.read_csv(window_file)
        feats = extract_basic_features(window_df, signal_column=signal_column)

        feats["record_name"] = record_name
        feats["window_file"] = window_file.name
        feats["signal_column_used"] = signal_column
        feats["available_signals"] = "|".join(signal_names)
        feats["sampling_rate"] = metadata["sampling_rate"]
        feats["num_samples_record"] = metadata["num_samples"]
        feats["comments"] = " | ".join(comments)

        rows.append(feats)

    features_df = pd.DataFrame(rows)

    output_file = PROCESSED_DIR / f"{record_name}_features.csv"
    features_df.to_csv(output_file, index=False)

    print(f"[INFO] Feature table saved to: {output_file}")
    print(f"[INFO] Number of windows processed: {len(features_df)}")
    return output_file


if __name__ == "__main__":
    build_feature_table("100")