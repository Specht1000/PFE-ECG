import json
from pathlib import Path

from src.config import (
    RAW_MITBIH_DIR,
    CSV_DIR,
    ensure_directories,
)
from src.dataset.read_mitbih import load_record


def convert_record_to_csv(record_name: str) -> Path:
    """
    Convert one MIT-BIH record to CSV and save metadata as JSON.
    """
    ensure_directories()

    signal_df, metadata = load_record(record_name, RAW_MITBIH_DIR)

    output_file = CSV_DIR / f"{record_name}.csv"
    signal_df.to_csv(output_file, index=False)

    meta_file = CSV_DIR / f"{record_name}_meta.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, default=str)

    print(f"[INFO] Record {record_name} converted successfully.")
    print(f"[INFO] Output file: {output_file}")
    print(f"[INFO] Number of samples: {metadata['num_samples']}")
    print(f"[INFO] Signal names: {metadata['signal_names']}")
    print(f"[INFO] Comments: {metadata['comments']}")

    return output_file


if __name__ == "__main__":
    convert_record_to_csv("100")