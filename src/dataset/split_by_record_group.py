from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

from src.config import PROCESSED_DIR, ensure_directories


def get_base_record_name(record_name: str) -> str:
    """
    Map transformed records to their original base record.

    Examples:
    - "233"   -> "233"
    - "x_233" -> "233"
    """
    if record_name.startswith("x_"):
        return record_name[2:]
    return record_name


def split_groups(
    base_records: List[str],
    test_size: float = 0.2
) -> Tuple[List[str], List[str]]:
    """
    Split base record groups into train and test sets.
    """
    if not base_records:
        raise ValueError("No base records provided for grouping.")

    base_records = sorted(base_records)
    split_index = int(len(base_records) * (1 - test_size))

    if split_index <= 0 or split_index >= len(base_records):
        raise ValueError("Invalid split. Adjust test_size.")

    train_groups = base_records[:split_index]
    test_groups = base_records[split_index:]

    return train_groups, test_groups


def split_dataset_by_group(
    input_file: Path = None,
    train_output: Path = None,
    test_output: Path = None,
    test_size: float = 0.2
) -> Tuple[Path, Path]:
    """
    Split dataset by base record group, ensuring that original and transformed
    versions of the same record stay together.
    """
    ensure_directories()

    if input_file is None:
        input_file = PROCESSED_DIR / "rr_features_labeled.csv"

    if train_output is None:
        train_output = PROCESSED_DIR / "rr_train_grouped.csv"

    if test_output is None:
        test_output = PROCESSED_DIR / "rr_test_grouped.csv"

    if not input_file.exists():
        raise FileNotFoundError(f"Input dataset not found: {input_file}")

    df = pd.read_csv(input_file)

    if "record_name" not in df.columns:
        raise ValueError("Dataset must contain a 'record_name' column.")

    if "label" not in df.columns:
        raise ValueError("Dataset must contain a 'label' column.")

    df["base_record"] = df["record_name"].apply(get_base_record_name)

    unique_base_records = sorted(df["base_record"].dropna().unique().tolist())

    train_groups, test_groups = split_groups(unique_base_records, test_size=test_size)

    train_df = df[df["base_record"].isin(train_groups)].copy()
    test_df = df[df["base_record"].isin(test_groups)].copy()

    train_df.to_csv(train_output, index=False)
    test_df.to_csv(test_output, index=False)

    print(f"[INFO] Total unique base records: {len(unique_base_records)}")
    print(f"[INFO] Train groups: {len(train_groups)}")
    print(f"[INFO] Test groups: {len(test_groups)}")

    print(f"[INFO] Train dataset saved to: {train_output}")
    print(f"[INFO] Test dataset saved to: {test_output}")

    print("\n[INFO] Train label distribution:")
    print(train_df["label"].value_counts())

    print("\n[INFO] Test label distribution:")
    print(test_df["label"].value_counts())

    print("\n[INFO] Train base groups:")
    print(train_groups)

    print("\n[INFO] Test base groups:")
    print(test_groups)

    print("\n[INFO] Example grouped records in train:")
    grouped_train_example = (
        train_df[["record_name", "base_record"]]
        .drop_duplicates()
        .sort_values(["base_record", "record_name"])
    )
    print(grouped_train_example.head(20).to_string(index=False))

    print("\n[INFO] Example grouped records in test:")
    grouped_test_example = (
        test_df[["record_name", "base_record"]]
        .drop_duplicates()
        .sort_values(["base_record", "record_name"])
    )
    print(grouped_test_example.head(20).to_string(index=False))

    return train_output, test_output


if __name__ == "__main__":
    split_dataset_by_group()