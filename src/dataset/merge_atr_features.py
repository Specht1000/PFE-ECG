from pathlib import Path
from typing import Optional, List

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

DEFAULT_WINDOW_SIZE_SAMPLES = 3600


def merge_all_atr_feature_files(
    output_filename: str = "atr_training_dataset.csv",
) -> Path:
    """
    Junta apenas os ATR puros:
    exemplo: 100_atr_features.csv
    exclui: 100_rr_atr_features.csv
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(
        f for f in PROCESSED_DIR.glob("*_atr_features.csv")
        if not f.name.endswith("_rr_atr_features.csv")
    )

    if not csv_files:
        raise FileNotFoundError(
            f"No pure *_atr_features.csv files found in {PROCESSED_DIR}"
        )

    frames = []
    for file in csv_files:
        df = pd.read_csv(file)
        if not df.empty:
            frames.append(df)

    if not frames:
        raise ValueError("ATR feature files were found, but all are empty.")

    merged_df = pd.concat(frames, ignore_index=True)

    output_file = PROCESSED_DIR / output_filename
    merged_df.to_csv(output_file, index=False)

    print(f"[OK] Merged ATR dataset saved to: {output_file}")
    print(f"[INFO] Rows: {len(merged_df)}")
    print(f"[INFO] Source files: {len(csv_files)}")

    return output_file


def merge_all_rr_atr_feature_files(
    output_filename: str = "rr_atr_training_dataset.csv",
) -> Path:
    """
    Junta apenas os arquivos RR+ATR:
    exemplo: 100_rr_atr_features.csv
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(PROCESSED_DIR.glob("*_rr_atr_features.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No *_rr_atr_features.csv files found in {PROCESSED_DIR}"
        )

    frames = []
    for file in csv_files:
        df = pd.read_csv(file)
        if not df.empty:
            frames.append(df)

    if not frames:
        raise ValueError("RR+ATR feature files were found, but all are empty.")

    merged_df = pd.concat(frames, ignore_index=True)

    output_file = PROCESSED_DIR / output_filename
    merged_df.to_csv(output_file, index=False)

    print(f"[OK] Merged RR+ATR dataset saved to: {output_file}")
    print(f"[INFO] Rows: {len(merged_df)}")
    print(f"[INFO] Source files: {len(csv_files)}")

    return output_file


def build_atr_labeled_dataset(
    output_filename: str = "atr_training_dataset.csv",
) -> Path:
    return merge_all_atr_feature_files(output_filename=output_filename)


def _find_rr_files(rr_file: Optional[Path] = None) -> List[Path]:
    if rr_file is not None:
        rr_path = Path(rr_file)
        if rr_path.exists():
            return [rr_path]
        raise FileNotFoundError(f"RR dataset file not found: {rr_path}")

    candidates = [
        PROCESSED_DIR / "rr_train_grouped.csv",
        PROCESSED_DIR / "rr_test_grouped.csv",
        PROCESSED_DIR / "rr_training_dataset.csv",
        PROCESSED_DIR / "rr_dataset.csv",
    ]

    found = [candidate for candidate in candidates if candidate.exists()]

    if not found:
        raise FileNotFoundError(
            f"No RR dataset files found in {PROCESSED_DIR}. "
            f"Expected one of: {[c.name for c in candidates]}"
        )

    return found


def _load_all_rr_data(rr_file: Optional[Path] = None) -> pd.DataFrame:
    rr_files = _find_rr_files(rr_file)

    frames = []
    for file in rr_files:
        df = pd.read_csv(file)
        if not df.empty:
            df = df.copy()
            df["__source_rr_file"] = file.name
            frames.append(df)

    if not frames:
        raise ValueError("RR dataset files were found, but all are empty.")

    return pd.concat(frames, ignore_index=True)


def _extract_window_index(window_file: str) -> int:
    name = Path(str(window_file)).stem
    parts = name.split("_window_")
    if len(parts) != 2:
        raise ValueError(f"Invalid window_file format: {window_file}")
    return int(parts[1])


def _list_atr_feature_files() -> List[Path]:
    return sorted(
        f for f in PROCESSED_DIR.glob("*_atr_features.csv")
        if not f.name.endswith("_rr_atr_features.csv")
    )


def _alternate_record_names(record_name: str) -> List[str]:
    record_name = str(record_name).strip()
    names = [record_name]

    if record_name.startswith("x_"):
        names.append(record_name[2:])
    else:
        names.append(f"x_{record_name}")

    seen = set()
    out = []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def build_window_level_atr_features(
    rr_file: Optional[Path] = None,
    output_filename: str = "atr_window_training_dataset.csv",
    window_size_samples: int = DEFAULT_WINDOW_SIZE_SAMPLES,
) -> Path:
    rr_df = _load_all_rr_data(rr_file)

    if rr_df.empty:
        raise ValueError("RR dataset is empty after loading all available RR files.")

    required_rr_cols = {"record_name", "window_file"}
    missing_rr = required_rr_cols - set(rr_df.columns)
    if missing_rr:
        raise KeyError(
            f"RR dataset missing required columns: {sorted(missing_rr)}"
        )

    atr_files = _list_atr_feature_files()
    if not atr_files:
        raise FileNotFoundError(
            f"No *_atr_features.csv files found in {PROCESSED_DIR}"
        )

    rr_df = rr_df.copy()
    rr_df["record_name"] = rr_df["record_name"].astype(str).str.strip()
    rr_df["window_index"] = rr_df["window_file"].apply(_extract_window_index)

    all_window_rows = []

    for atr_file in atr_files:
        atr_df = pd.read_csv(atr_file)
        if atr_df.empty:
            continue

        if "record_name" not in atr_df.columns or "sample" not in atr_df.columns:
            continue

        atr_df = atr_df.copy()
        atr_df["record_name"] = atr_df["record_name"].astype(str).str.strip()

        record_name = atr_df["record_name"].iloc[0]
        candidate_names = _alternate_record_names(record_name)

        rr_record = rr_df.loc[rr_df["record_name"].isin(candidate_names)].copy()

        if rr_record.empty:
            continue

        atr_df["window_index"] = (atr_df["sample"] // window_size_samples).astype(int)

        grouped = atr_df.groupby(["record_name", "window_index"], dropna=False)

        window_features = grouped.agg(
            atr_num_annotations=("sample", "count"),
            atr_num_normal=("beat_class", lambda s: int((s == "normal").sum())),
            atr_num_supraventricular=("beat_class", lambda s: int((s == "supraventricular").sum())),
            atr_num_ventricular=("beat_class", lambda s: int((s == "ventricular").sum())),
            atr_num_fusion=("beat_class", lambda s: int((s == "fusion").sum())),
            atr_num_other=("beat_class", lambda s: int((s == "other").sum())),
            atr_num_unknown=("beat_class", lambda s: int((s == "unknown").sum())),
        ).reset_index()

        duplicated_rows = []
        for alt_name in candidate_names:
            tmp = window_features.copy()
            tmp["record_name"] = alt_name
            duplicated_rows.append(tmp)
        window_features = pd.concat(duplicated_rows, ignore_index=True)

        window_features["atr_has_normal"] = (window_features["atr_num_normal"] > 0).astype(int)
        window_features["atr_has_supraventricular"] = (window_features["atr_num_supraventricular"] > 0).astype(int)
        window_features["atr_has_ventricular"] = (window_features["atr_num_ventricular"] > 0).astype(int)
        window_features["atr_has_fusion"] = (window_features["atr_num_fusion"] > 0).astype(int)
        window_features["atr_has_other"] = (window_features["atr_num_other"] > 0).astype(int)
        window_features["atr_has_unknown"] = (window_features["atr_num_unknown"] > 0).astype(int)

        merged = pd.merge(
            rr_record,
            window_features,
            on=["record_name", "window_index"],
            how="left",
        )

        atr_cols = [
            "atr_num_annotations",
            "atr_num_normal",
            "atr_num_supraventricular",
            "atr_num_ventricular",
            "atr_num_fusion",
            "atr_num_other",
            "atr_num_unknown",
            "atr_has_normal",
            "atr_has_supraventricular",
            "atr_has_ventricular",
            "atr_has_fusion",
            "atr_has_other",
            "atr_has_unknown",
        ]

        for col in atr_cols:
            if col in merged.columns:
                merged[col] = merged[col].fillna(0).astype(int)

        all_window_rows.append(merged)

    if not all_window_rows:
        raise ValueError(
            "No compatible ATR/RR records found to build window-level ATR features."
        )

    final_df = pd.concat(all_window_rows, ignore_index=True)

    output_file = PROCESSED_DIR / output_filename
    final_df.to_csv(output_file, index=False)

    print(f"[OK] Window-level ATR dataset saved to: {output_file}")
    print(f"[INFO] Rows: {len(final_df)}")

    return output_file


def merge_rr_with_atr(
    record_name: Optional[str] = None,
    rr_file: Optional[Path] = None,
    atr_file: Optional[Path] = None,
    output_filename: Optional[str] = None,
    window_size_samples: int = DEFAULT_WINDOW_SIZE_SAMPLES,
) -> Path:
    rr_df = _load_all_rr_data(rr_file)

    if atr_file is None:
        atr_file = build_window_level_atr_features(
            rr_file=rr_file,
            output_filename="atr_window_training_dataset.csv",
            window_size_samples=window_size_samples,
        )
    else:
        atr_file = Path(atr_file)

    atr_df = pd.read_csv(atr_file)

    required_keys = {"record_name", "window_file"}
    missing_rr = required_keys - set(rr_df.columns)
    missing_atr = required_keys - set(atr_df.columns)

    if missing_rr:
        raise KeyError(f"RR dataset missing merge columns: {sorted(missing_rr)}")
    if missing_atr:
        raise KeyError(f"ATR dataset missing merge columns: {sorted(missing_atr)}")

    rr_df = rr_df.copy()
    atr_df = atr_df.copy()

    rr_df["record_name"] = rr_df["record_name"].astype(str).str.strip()
    atr_df["record_name"] = atr_df["record_name"].astype(str).str.strip()

    if record_name is not None:
        candidate_names = _alternate_record_names(record_name)
        rr_df = rr_df.loc[rr_df["record_name"].isin(candidate_names)].copy()
        atr_df = atr_df.loc[atr_df["record_name"].isin(candidate_names)].copy()

        if rr_df.empty:
            raise ValueError(f"No RR rows found for record '{record_name}'")

        if atr_df.empty:
            raise ValueError(f"No ATR rows found for record '{record_name}'")

    drop_cols = [
        c for c in rr_df.columns
        if c in atr_df.columns and c not in ["record_name", "window_file"]
    ]

    merged_df = pd.merge(
        rr_df,
        atr_df.drop(columns=drop_cols, errors="ignore"),
        on=["record_name", "window_file"],
        how="left",
    )

    if output_filename is None:
        output_filename = (
            f"{record_name}_rr_atr_features.csv"
            if record_name is not None
            else "rr_atr_training_dataset.csv"
        )

    output_file = PROCESSED_DIR / output_filename
    merged_df.to_csv(output_file, index=False)

    print(f"[OK] RR + ATR merged dataset saved to: {output_file}")
    print(f"[INFO] RR rows: {len(rr_df)}")
    print(f"[INFO] ATR rows: {len(atr_df)}")
    print(f"[INFO] Merged rows: {len(merged_df)}")

    return output_file


if __name__ == "__main__":
    atr_file = build_atr_labeled_dataset()
    print(f"[INFO] ATR merged file: {atr_file}")