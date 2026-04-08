import argparse
from pathlib import Path

from src.config import (
    DEFAULT_RECORD,
    DEFAULT_SIGNAL_COLUMN,
    RAW_MITBIH_DIR,
    ensure_directories,
)
from src.dataset.convert_to_csv import convert_record_to_csv
from src.dataset.read_mitbih import load_record
from src.preprocessing.windowing import create_windows_from_csv
from src.features.feature_builder import build_feature_table
from scripts.setup_mitbih import extract_mitbih_zip


def dataset_is_available(record: str = DEFAULT_RECORD) -> bool:
    """
    Check if the MIT-BIH dataset has already been extracted.
    """
    dat_file = RAW_MITBIH_DIR / f"{record}.dat"
    hea_file = RAW_MITBIH_DIR / f"{record}.hea"
    return dat_file.exists() and hea_file.exists()


def step_setup(zip_path: str, force: bool = False) -> None:
    """
    Extract the dataset only if needed.
    """
    if dataset_is_available() and not force:
        print("[STEP] Dataset already available. Skipping extraction.")
        return

    print("[STEP] Extracting MIT-BIH dataset...")
    extract_mitbih_zip(Path(zip_path))
    print("[DONE] Dataset extraction completed.\n")


def step_read(record: str) -> None:
    print(f"[STEP] Reading record {record}...")
    df, meta = load_record(record, RAW_MITBIH_DIR)

    print(f"[INFO] Record: {meta['record_name']}")
    print(f"[INFO] Shape: {df.shape}")
    print(f"[INFO] Sampling rate: {meta['sampling_rate']}")
    print(f"[INFO] Columns: {df.columns.tolist()}")
    print(df.head())
    print("[DONE] Record read completed.\n")


def step_convert(record: str) -> None:
    print(f"[STEP] Converting record {record} to CSV...")
    convert_record_to_csv(record)
    print("[DONE] CSV conversion completed.\n")


def step_window(record: str, signal_column: str) -> None:
    print(f"[STEP] Creating windows for record {record}...")
    create_windows_from_csv(record, signal_column=signal_column)
    print("[DONE] Windowing completed.\n")


def step_features(record: str, signal_column: str) -> None:
    print(f"[STEP] Building features for record {record}...")
    build_feature_table(record, signal_column=signal_column)
    print("[DONE] Feature extraction completed.\n")


def step_all(record: str, signal_column: str) -> None:
    """
    Run the full pipeline except dataset extraction.
    Assumes dataset is already available.
    """
    if not dataset_is_available(record):
        raise FileNotFoundError(
            f"Dataset for record {record} not found in {RAW_MITBIH_DIR}. "
            f"Run setup first."
        )

    step_read(record)
    step_convert(record)
    step_window(record, signal_column)
    step_features(record, signal_column)
    print("[SUCCESS] Full pipeline completed successfully.")


def main():
    ensure_directories()

    parser = argparse.ArgumentParser(
        description="MIT-BIH ECG project pipeline runner"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # setup
    parser_setup = subparsers.add_parser("setup", help="Extract and organize MIT-BIH zip")
    parser_setup.add_argument(
        "--zip",
        type=str,
        default="mit-bih-arrhythmia-database-1.0.0.zip",
        help="Path to MIT-BIH zip file"
    )
    parser_setup.add_argument(
        "--force",
        action="store_true",
        help="Force re-extraction even if dataset already exists"
    )

    # read
    parser_read = subparsers.add_parser("read", help="Read one MIT-BIH record")
    parser_read.add_argument("--record", type=str, default=DEFAULT_RECORD)

    # convert
    parser_convert = subparsers.add_parser("convert", help="Convert one MIT-BIH record to CSV")
    parser_convert.add_argument("--record", type=str, default=DEFAULT_RECORD)

    # window
    parser_window = subparsers.add_parser("window", help="Create windows from one CSV record")
    parser_window.add_argument("--record", type=str, default=DEFAULT_RECORD)
    parser_window.add_argument("--signal", type=str, default=DEFAULT_SIGNAL_COLUMN)

    # features
    parser_features = subparsers.add_parser("features", help="Extract features from windows")
    parser_features.add_argument("--record", type=str, default=DEFAULT_RECORD)
    parser_features.add_argument("--signal", type=str, default=DEFAULT_SIGNAL_COLUMN)

    # all
    parser_all = subparsers.add_parser("all", help="Run the processing pipeline (without extraction)")
    parser_all.add_argument("--record", type=str, default=DEFAULT_RECORD)
    parser_all.add_argument("--signal", type=str, default=DEFAULT_SIGNAL_COLUMN)

    args = parser.parse_args()

    if args.command == "setup":
        step_setup(args.zip, force=args.force)
    elif args.command == "read":
        step_read(args.record)
    elif args.command == "convert":
        step_convert(args.record)
    elif args.command == "window":
        step_window(args.record, args.signal)
    elif args.command == "features":
        step_features(args.record, args.signal)
    elif args.command == "all":
        step_all(args.record, args.signal)


if __name__ == "__main__":
    main()