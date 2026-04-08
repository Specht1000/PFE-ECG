from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

ARR_FILE = PROCESSED_DIR / "rr_atr_arrhythmia_dataset.csv"
MORPH_FILE = PROCESSED_DIR / "ecg_morphological_features.csv"
OUTPUT_FILE = PROCESSED_DIR / "rr_atr_arrhythmia_morph_dataset.csv"


def main():
    print("[STEP 1] Loading datasets...")
    arr_df = pd.read_csv(ARR_FILE)
    morph_df = pd.read_csv(MORPH_FILE)

    print(f"[INFO] Arrhythmia dataset: {arr_df.shape}")
    print(f"[INFO] Morph dataset: {morph_df.shape}")

    merged = pd.merge(
        arr_df,
        morph_df,
        on=["record_name", "window_file"],
        how="left",
    )

    morph_cols = [c for c in merged.columns if c.startswith("morph_")]
    for col in morph_cols:
        merged[col] = merged[col].fillna(0)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUTPUT_FILE, index=False)

    print(f"[OK] Saved merged dataset to: {OUTPUT_FILE}")
    print(f"[INFO] Output shape: {merged.shape}")


if __name__ == "__main__":
    main()