from pathlib import Path

from src.dataset.build_atr_labels import build_atr_label_table
from src.dataset.merge_atr_features import (
    merge_all_atr_feature_files,
    build_atr_labeled_dataset,
    merge_rr_with_atr,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def discover_records():
    """
    Descobre automaticamente registros WFDB a partir dos arquivos .atr.
    """
    records = set()

    if not RAW_DIR.exists():
        raise FileNotFoundError(f"RAW_DIR not found: {RAW_DIR}")

    for atr_file in RAW_DIR.rglob("*.atr"):
        records.add(atr_file.stem)

    return sorted(records)


def main():
    print("[STEP 1] Discovering records...")
    records = discover_records()

    if not records:
        raise FileNotFoundError(f"No .atr records found under {RAW_DIR}")

    print(f"[INFO] Total records found: {len(records)}")

    for record_name in records:
        print(f"\n[RECORD] Processing ATR labels for record {record_name}")

        try:
            print("[STEP] Building ATR labels...")
            build_atr_label_table(record_name)

            print("[STEP] Merging RR features with ATR labels...")
            try:
                merge_rr_with_atr(record_name=record_name)
            except Exception as merge_err:
                print(f"[ERROR] Failed to process record {record_name}: {merge_err}")

        except Exception as e:
            print(f"[ERROR] Failed to process record {record_name}: {e}")

    print("\n[STEP 2] Merging all ATR feature files...")
    merged_file = merge_all_atr_feature_files()
    print(f"[INFO] Merged ATR file: {merged_file}")

    print("\n[STEP 3] Building final ATR labeled dataset...")
    final_file = build_atr_labeled_dataset()
    print(f"[INFO] Final ATR labeled dataset: {final_file}")

    print("\n[SUCCESS] ATR training dataset build completed successfully.")


if __name__ == "__main__":
    main()