from pathlib import Path
import pandas as pd

from src.config import PROCESSED_DIR, ensure_directories


def assign_simple_labels(input_file: Path, output_file: Path = None) -> Path:
    """
    Create simple automatic labels based on basic signal statistics.

    This is only an initial placeholder labeling strategy.
    It should be replaced later by labels based on RR intervals
    or MIT-BIH annotations.
    """
    ensure_directories()

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    df = pd.read_csv(input_file)

    required_columns = {"std", "range", "energy"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    labels = []

    for _, row in df.iterrows():
        std_val = row["std"]
        range_val = row["range"]
        energy_val = row["energy"]

        if std_val < 0.08 and range_val < 0.8:
            label = "bradycardia"
        elif std_val > 0.20 and energy_val > 200:
            label = "tachycardia"
        elif std_val > 0.12 and range_val > 1.0:
            label = "possible_af"
        else:
            label = "normal"

        labels.append(label)

    df["label"] = labels

    if output_file is None:
        output_file = PROCESSED_DIR / "features_labeled.csv"

    df.to_csv(output_file, index=False)

    print(f"[INFO] Labeled dataset saved to: {output_file}")
    print("[INFO] Label distribution:")
    print(df["label"].value_counts())

    return output_file


if __name__ == "__main__":
    input_path = PROCESSED_DIR / "features_all.csv"
    assign_simple_labels(input_path)