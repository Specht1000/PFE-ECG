import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from src.config import WINDOWS_DIR, PROCESSED_DIR, CSV_DIR, ensure_directories
from src.utils.signal_utils import choose_best_signal_column
from src.signal_processing.pan_tompkins import detect_r_peaks, compute_rr_intervals


def extract_signal_statistics(signal: np.ndarray) -> Dict[str, float]:
    return {
        "mean": float(np.mean(signal)),
        "std": float(np.std(signal)),
        "min": float(np.min(signal)),
        "max": float(np.max(signal)),
        "range": float(np.max(signal) - np.min(signal)),
        "energy": float(np.sum(signal ** 2)),
    }


def extract_rr_features(signal: np.ndarray, fs: int) -> Dict[str, float]:
    result = detect_r_peaks(signal, fs)
    r_peaks = result["r_peaks"]
    rr = compute_rr_intervals(r_peaks, fs)

    features = {
        "num_r_peaks": int(len(r_peaks)),
        "num_rr_intervals": int(len(rr)),
    }

    if len(rr) == 0:
        features.update({
            "rr_mean": np.nan,
            "rr_std": np.nan,
            "rr_min": np.nan,
            "rr_max": np.nan,
            "rr_cv": np.nan,
            "hr_mean_bpm": np.nan,
            "hr_std_bpm": np.nan,
        })
        return features

    hr = 60.0 / rr

    features.update({
        "rr_mean": float(np.mean(rr)),
        "rr_std": float(np.std(rr)),
        "rr_min": float(np.min(rr)),
        "rr_max": float(np.max(rr)),
        "rr_cv": float(np.std(rr) / np.mean(rr)) if np.mean(rr) > 0 else np.nan,
        "hr_mean_bpm": float(np.mean(hr)),
        "hr_std_bpm": float(np.std(hr)),
    })

    return features


def assign_rr_based_label(rr_features: Dict[str, float]) -> str:
    """
    Provisional rule-based label using physiological features.
    This is much better than the old std/range-based fake labels,
    but still not the final clinical ground truth.
    """

    hr_mean = rr_features.get("hr_mean_bpm")
    rr_cv = rr_features.get("rr_cv")
    num_rr = rr_features.get("num_rr_intervals", 0)

    if num_rr < 3 or np.isnan(hr_mean):
        return "unclassified"

    if hr_mean < 60:
        return "bradycardia"
    if hr_mean > 100:
        return "tachycardia"
    if rr_cv is not None and not np.isnan(rr_cv) and rr_cv > 0.12:
        return "possible_af"

    return "normal"


def build_rr_feature_table(record_name: str, signal_column: str = None) -> Path:
    ensure_directories()

    meta_file = CSV_DIR / f"{record_name}_meta.json"
    if not meta_file.exists():
        raise FileNotFoundError(f"Metadata file not found: {meta_file}")

    with open(meta_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    signal_names = metadata["signal_names"]
    comments = metadata.get("comments", [])
    fs = int(metadata["sampling_rate"])

    if signal_column is None:
        signal_column = choose_best_signal_column(signal_names)

    window_files = sorted(WINDOWS_DIR.glob(f"{record_name}_window_*.csv"))
    if not window_files:
        raise FileNotFoundError(f"No windows found for record {record_name} in {WINDOWS_DIR}")

    rows: List[Dict[str, float]] = []

    for window_file in window_files:
        window_df = pd.read_csv(window_file)

        if signal_column not in window_df.columns:
            continue

        signal = window_df[signal_column].to_numpy()

        row = {}
        row.update(extract_signal_statistics(signal))
        rr_feats = extract_rr_features(signal, fs)
        row.update(rr_feats)

        row["record_name"] = record_name
        row["window_file"] = window_file.name
        row["signal_column_used"] = signal_column
        row["available_signals"] = "|".join(signal_names)
        row["sampling_rate"] = fs
        row["num_samples_record"] = metadata["num_samples"]
        row["comments"] = " | ".join(comments)
        row["label"] = assign_rr_based_label(rr_feats)

        rows.append(row)

    features_df = pd.DataFrame(rows)

    output_file = PROCESSED_DIR / f"{record_name}_rr_features.csv"
    features_df.to_csv(output_file, index=False)

    print(f"[INFO] RR feature table saved to: {output_file}")
    print(f"[INFO] Number of windows processed: {len(features_df)}")

    if "label" in features_df.columns:
        print("[INFO] Label distribution:")
        print(features_df["label"].value_counts(dropna=False))

    return output_file


if __name__ == "__main__":
    build_rr_feature_table("100")