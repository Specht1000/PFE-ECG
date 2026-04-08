from src.config import ensure_directories, RAW_MITBIH_DIR
from src.dataset.read_mitbih import get_available_records
from src.dataset.convert_to_csv import convert_record_to_csv
from src.preprocessing.windowing import create_windows_from_csv
from src.features.rr_features import build_rr_feature_table
from src.dataset.build_rr_dataset import merge_rr_feature_files, build_rr_labeled_dataset


def run_rr_batch(records=None):
    ensure_directories()

    if records is None:
        records = get_available_records(RAW_MITBIH_DIR)

    print(f"[INFO] Total records found: {len(records)}")

    for record in records:
        print(f"\n[RECORD] Processing record {record}")

        try:
            print("[STEP] Converting to CSV...")
            convert_record_to_csv(record)

            print("[STEP] Creating windows...")
            create_windows_from_csv(record)

            print("[STEP] Building RR features...")
            build_rr_feature_table(record)

            print(f"[DONE] Record {record} processed successfully.")

        except Exception as exc:
            print(f"[ERROR] Failed to process record {record}: {exc}")


def main():
    ensure_directories()

    print("[STEP 1] Running RR batch pipeline for all available records...")
    run_rr_batch()

    print("\n[STEP 2] Merging RR feature files...")
    merged_file = merge_rr_feature_files()

    print("\n[STEP 3] Building final RR labeled dataset...")
    build_rr_labeled_dataset(merged_file)

    print("\n[SUCCESS] RR training dataset build completed successfully.")


if __name__ == "__main__":
    main()