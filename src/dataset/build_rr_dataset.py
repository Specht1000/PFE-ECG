from pathlib import Path
import pandas as pd

from src.config import PROCESSED_DIR, ensure_directories


def merge_rr_feature_files(output_name: str = "rr_features_all.csv") -> Path:
    ensure_directories()

    feature_files = sorted(PROCESSED_DIR.glob("*_rr_features.csv"))

    if not feature_files:
        raise FileNotFoundError(f"No RR feature files found in {PROCESSED_DIR}")

    dfs = []
    for file_path in feature_files:
        df = pd.read_csv(file_path)
        dfs.append(df)

    merged_df = pd.concat(dfs, ignore_index=True)

    output_file = PROCESSED_DIR / output_name
    merged_df.to_csv(output_file, index=False)

    print(f"[INFO] Merged RR dataset saved to: {output_file}")
    print(f"[INFO] Total rows: {len(merged_df)}")
    print(f"[INFO] Total columns: {len(merged_df.columns)}")

    return output_file


def build_rr_labeled_dataset(input_file: Path = None, output_name: str = "rr_features_labeled.csv") -> Path:
    ensure_directories()

    if input_file is None:
        input_file = PROCESSED_DIR / "rr_features_all.csv"

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    df = pd.read_csv(input_file)

    if "label" not in df.columns:
        raise ValueError("Input RR dataset must contain a 'label' column.")

    df = df[df["label"] != "unclassified"].copy()

    output_file = PROCESSED_DIR / output_name
    df.to_csv(output_file, index=False)

    print(f"[INFO] Final RR labeled dataset saved to: {output_file}")
    print("[INFO] Label distribution:")
    print(df["label"].value_counts())

    return output_file


if __name__ == "__main__":
    merged = merge_rr_feature_files()
    build_rr_labeled_dataset(merged)