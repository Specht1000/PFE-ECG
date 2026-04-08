from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    rr_atr_files = sorted(PROCESSED_DIR.glob("*_rr_atr_features.csv"))

    if not rr_atr_files:
        raise FileNotFoundError(
            f"No *_rr_atr_features.csv files found in {PROCESSED_DIR}"
        )

    frames = []
    for file in rr_atr_files:
        df = pd.read_csv(file)

        if df.empty:
            continue

        df = df.copy()
        df["source_file"] = file.name
        frames.append(df)

    if not frames:
        raise ValueError("RR+ATR files were found, but all are empty.")

    merged_df = pd.concat(frames, ignore_index=True)

    output_file = PROCESSED_DIR / "rr_atr_training_dataset.csv"
    merged_df.to_csv(output_file, index=False)

    print(f"[OK] Merged RR+ATR dataset saved to: {output_file}")
    print(f"[INFO] Source files: {len(rr_atr_files)}")
    print(f"[INFO] Rows: {len(merged_df)}")
    print(f"[INFO] Columns: {len(merged_df.columns)}")


if __name__ == "__main__":
    main()