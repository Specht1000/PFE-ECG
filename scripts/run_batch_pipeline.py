from src.config import ensure_directories, RAW_MITBIH_DIR
from src.dataset.convert_to_csv import convert_record_to_csv
from src.dataset.read_mitbih import get_available_records
from src.preprocessing.windowing import create_windows_from_csv
from src.features.feature_builder import build_feature_table


def run_batch(records=None):
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

            print("[STEP] Building features...")
            build_feature_table(record)

            print(f"[DONE] Record {record} processed successfully.")

        except Exception as exc:
            print(f"[ERROR] Failed to process record {record}: {exc}")


if __name__ == "__main__":
    run_batch()