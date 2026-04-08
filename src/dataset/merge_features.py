from pathlib import Path
import pandas as pd

from src.config import PROCESSED_DIR, ensure_directories


def merge_feature_files(output_name: str = "features_all.csv") -> Path:
    ensure_directories()

    feature_files = sorted(PROCESSED_DIR.glob("*_features.csv"))

    if not feature_files:
        raise FileNotFoundError(f"No feature files found in {PROCESSED_DIR}")

    dfs = []
    for file_path in feature_files:
        df = pd.read_csv(file_path)
        dfs.append(df)

    merged_df = pd.concat(dfs, ignore_index=True)

    output_file = PROCESSED_DIR / output_name
    merged_df.to_csv(output_file, index=False)

    print(f"[INFO] Merged dataset saved to: {output_file}")
    print(f"[INFO] Total rows: {len(merged_df)}")
    print(f"[INFO] Total columns: {len(merged_df.columns)}")

    return output_file


if __name__ == "__main__":
    merge_feature_files()