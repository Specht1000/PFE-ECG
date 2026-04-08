from pathlib import Path
from typing import Union

import pandas as pd
import wfdb


PathLike = Union[str, Path]

# Classes gerais de batimentos/anotações do MIT-BIH
NORMAL_SYMBOLS = {"N", "L", "R", "e", "j"}
SUPRAVENTRICULAR_SYMBOLS = {"A", "a", "J", "S"}
VENTRICULAR_SYMBOLS = {"V", "E"}
FUSION_SYMBOLS = {"F"}
UNKNOWN_SYMBOLS = {"/", "f", "Q", "?"}


def classify_annotation_symbol(symbol: str) -> str:
    """
    Classifica o símbolo de anotação em uma classe geral.
    """
    if not isinstance(symbol, str):
        return "unknown"

    symbol = symbol.strip()

    if symbol in NORMAL_SYMBOLS:
        return "normal"
    if symbol in SUPRAVENTRICULAR_SYMBOLS:
        return "supraventricular"
    if symbol in VENTRICULAR_SYMBOLS:
        return "ventricular"
    if symbol in FUSION_SYMBOLS:
        return "fusion"
    if symbol in UNKNOWN_SYMBOLS:
        return "unknown"

    return "other"


def load_annotations(record_path: PathLike, extension: str = "atr") -> pd.DataFrame:
    """
    Carrega as anotações WFDB de um registro e retorna um DataFrame padronizado.

    Exemplo:
        record_path = "data/raw/mitdb/100"
    """
    record_path = str(record_path)
    ann = wfdb.rdann(record_path, extension)

    n = len(ann.sample)

    def safe_attr(name, default=None):
        value = getattr(ann, name, None)
        if value is None:
            return [default] * n
        return list(value)

    aux_note = safe_attr("aux_note", "")
    aux_note = [x.strip() if isinstance(x, str) else "" for x in aux_note]

    df = pd.DataFrame(
        {
            "sample": list(ann.sample),
            "symbol": safe_attr("symbol", ""),
            "subtype": safe_attr("subtype", 0),
            "chan": safe_attr("chan", 0),
            "num": safe_attr("num", 0),
            "aux_note": aux_note,
        }
    )

    df["beat_class"] = df["symbol"].apply(classify_annotation_symbol)
    return df


def summarize_annotation_counts(
    annotations_df: pd.DataFrame,
    class_column: str = "beat_class",
    symbol_column: str = "symbol",
) -> dict:
    """
    Resume contagens das anotações em formato dicionário.

    Retorna algo como:
    {
        "total_annotations": 2274,
        "class_counts": {"normal": 2000, "ventricular": 150, ...},
        "symbol_counts": {"N": 1900, "V": 120, ...}
    }
    """
    if annotations_df is None or annotations_df.empty:
        return {
            "total_annotations": 0,
            "class_counts": {},
            "symbol_counts": {},
        }

    class_counts = {}
    symbol_counts = {}

    if class_column in annotations_df.columns:
        class_counts = (
            annotations_df[class_column]
            .value_counts(dropna=False)
            .to_dict()
        )

    if symbol_column in annotations_df.columns:
        symbol_counts = (
            annotations_df[symbol_column]
            .value_counts(dropna=False)
            .to_dict()
        )

    return {
        "total_annotations": int(len(annotations_df)),
        "class_counts": class_counts,
        "symbol_counts": symbol_counts,
    }


def load_annotation_samples(record_path: PathLike, extension: str = "atr"):
    return load_annotations(record_path, extension)["sample"].tolist()


def load_annotation_symbols(record_path: PathLike, extension: str = "atr"):
    return load_annotations(record_path, extension)["symbol"].tolist()