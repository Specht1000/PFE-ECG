from pathlib import Path
from typing import Dict, Tuple, List

import pandas as pd
import wfdb


def load_record(record_name: str, data_dir: Path) -> Tuple[pd.DataFrame, Dict]:
    """
    Load one MIT-BIH record and return:
    - a DataFrame with ECG signals
    - a metadata dictionary
    """
    record_path = data_dir / record_name

    dat_file = data_dir / f"{record_name}.dat"
    hea_file = data_dir / f"{record_name}.hea"

    if not dat_file.exists():
        raise FileNotFoundError(f"Missing file: {dat_file}")
    if not hea_file.exists():
        raise FileNotFoundError(f"Missing file: {hea_file}")

    record = wfdb.rdrecord(str(record_path))

    annotation_samples: List[int] = []
    annotation_symbols: List[str] = []

    atr_file = data_dir / f"{record_name}.atr"
    if atr_file.exists():
        ann = wfdb.rdann(str(record_path), "atr")
        annotation_samples = ann.sample.tolist()
        annotation_symbols = ann.symbol

    signal_df = pd.DataFrame(record.p_signal, columns=record.sig_name)
    signal_df["sample_index"] = range(len(signal_df))
    signal_df["time_s"] = signal_df["sample_index"] / record.fs

    metadata = {
        "record_name": record_name,
        "sampling_rate": record.fs,
        "signal_names": record.sig_name,
        "units": record.units,
        "num_samples": record.sig_len,
        "comments": record.comments,
        "annotation_samples": annotation_samples,
        "annotation_symbols": annotation_symbols,
    }

    return signal_df, metadata


def get_available_records(data_dir: Path):
    """
    Return all record names based on .hea files found in the dataset directory.
    """
    return sorted([p.stem for p in data_dir.glob("*.hea")])


if __name__ == "__main__":
    from src.config import RAW_MITBIH_DIR, DEFAULT_RECORD, ensure_directories

    ensure_directories()

    df, meta = load_record(DEFAULT_RECORD, RAW_MITBIH_DIR)

    print("[INFO] Record loaded successfully.")
    print(f"[INFO] Record: {meta['record_name']}")
    print(f"[INFO] Shape: {df.shape}")
    print(f"[INFO] Columns: {df.columns.tolist()}")
    print(f"[INFO] Sampling rate: {meta['sampling_rate']}")
    print(f"[INFO] Comments: {meta['comments']}")