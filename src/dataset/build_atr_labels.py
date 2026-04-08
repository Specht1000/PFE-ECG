from pathlib import Path
from typing import Optional

import pandas as pd

from src.dataset.annotations import (
    load_annotations,
    summarize_annotation_counts,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"


def _find_record_base_path(record_name: str) -> Path:
    """
    Procura o caminho base de um registro WFDB sem extensão.
    Exemplo de retorno:
        .../data/raw/mitdb/100
    """
    direct_candidates = [
        RAW_DIR / "mitdb" / record_name,
        RAW_DIR / record_name,
        RAW_DIR / "records" / record_name,
        RAW_DIR / "atr" / record_name,
    ]

    for base in direct_candidates:
        hea_file = base.with_suffix(".hea")
        dat_file = base.with_suffix(".dat")
        atr_file = base.with_suffix(".atr")

        if hea_file.exists() and dat_file.exists():
            return base
        if atr_file.exists():
            return base

    # busca recursiva
    for hea_file in RAW_DIR.rglob(f"{record_name}.hea"):
        return hea_file.with_suffix("")

    for atr_file in RAW_DIR.rglob(f"{record_name}.atr"):
        return atr_file.with_suffix("")

    raise FileNotFoundError(f"Record '{record_name}' not found under {RAW_DIR}")


def build_atr_label_table(record_name: str, output_dir: Optional[Path] = None) -> Path:
    """
    Gera o CSV de features/labels ATR para um registro.
    """
    if output_dir is None:
        output_dir = PROCESSED_DIR

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    record_base = _find_record_base_path(record_name)

    annotations_df = load_annotations(record_base, extension="atr")

    if annotations_df is None or annotations_df.empty:
        raise ValueError(f"No annotations found for record '{record_name}'")

    summary = summarize_annotation_counts(annotations_df)

    df = annotations_df.copy()
    df["record_name"] = record_name
    df["record_path"] = str(record_base)
    df["total_annotations"] = summary["total_annotations"]

    output_file = output_dir / f"{record_name}_atr_features.csv"
    df.to_csv(output_file, index=False)

    print(f"[OK] ATR labels saved to: {output_file}")
    print(f"[INFO] Total annotations: {summary['total_annotations']}")
    print(f"[INFO] Class counts: {summary['class_counts']}")

    return output_file


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m src.dataset.build_atr_labels <record_name>")

    build_atr_label_table(sys.argv[1])