from pathlib import Path
from typing import List, Tuple

import pandas as pd

from src.config import PROCESSED_DIR, ensure_directories


def split_records(
    records: List[str],
    test_size: float = 0.2
) -> Tuple[List[str], List[str]]:
    """
    Split record names into train and test sets without mixing windows
    from the same record in both sets.
    """
    if not records:
        raise ValueError("No records provided for splitting.")

    records = sorted(records)
    split_index = int(len(records) * (1 - test_size))

    if split_index <= 0 or split_index >= len(records):
        raise ValueError("Invalid split. Adjust test_size.")

    train_records = records[:split_index]
    test_records = records[split_index:]

    return train_records, test_records


def split_dataset_by_record(
    input_file: Path = None,
    train_output: Path = None,
    test_output: Path = None,
    test_size: float = 0.2
) -> Tuple[Path, Path]:
    """
    Split the RR labeled dataset by record_name and save train/test files.
    """
    ensure_directories()

    if input_file is None:
        input_file = PROCESSED_DIR / "rr_features_labeled.csv"

    if train_output is None:
        train_output = PROCESSED_DIR / "rr_train.csv"

    if test_output is None:
        test_output = PROCESSED_DIR / "rr_test.csv"

    if not input_file.exists():
        raise FileNotFoundError(f"Input dataset not found: {input_file}")

    df = pd.read_csv(input_file)

    if "record_name" not in df.columns:
        raise ValueError("Dataset must contain a 'record_name' column.")

    if "label" not in df.columns:
        raise ValueError("Dataset must contain a 'label' column.")

    unique_records = sorted(df["record_name"].dropna().unique().tolist())

    train_records, test_records = split_records(unique_records, test_size=test_size)

    train_df = df[df["record_name"].isin(train_records)].copy()
    test_df = df[df["record_name"].isin(test_records)].copy()

    train_df.to_csv(train_output, index=False)
    test_df.to_csv(test_output, index=False)

    print(f"[INFO] Total unique records: {len(unique_records)}")
    print(f"[INFO] Train records: {len(train_records)}")
    print(f"[INFO] Test records: {len(test_records)}")

    print(f"[INFO] Train dataset saved to: {train_output}")
    print(f"[INFO] Test dataset saved to: {test_output}")

    print("\n[INFO] Train label distribution:")
    print(train_df["label"].value_counts())

    print("\n[INFO] Test label distribution:")
    print(test_df["label"].value_counts())

    print("\n[INFO] Train records:")
    print(train_records)

    print("\n[INFO] Test records:")
    print(test_records)

    return train_output, test_output


if __name__ == "__main__":
    split_dataset_by_record()