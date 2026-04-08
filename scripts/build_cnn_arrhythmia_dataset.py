from pathlib import Path
import re

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
WINDOWS_DIR = PROJECT_ROOT / "data" / "interim" / "windows"

ARR_FILE = PROCESSED_DIR / "rr_atr_arrhythmia_dataset.csv"
OUTPUT_X = PROCESSED_DIR / "cnn_X.npy"
OUTPUT_Y = PROCESSED_DIR / "cnn_y.csv"


def choose_signal_column(df: pd.DataFrame) -> str:
    preferred = ["MLII", "V5", "V1", "ECG", "signal", "value"]
    for col in preferred:
        if col in df.columns:
            return col

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        raise ValueError("Nenhuma coluna numérica encontrada na janela.")
    return numeric_cols[0]


def locate_window_csv(window_file: str) -> Path:
    candidate = WINDOWS_DIR / window_file
    if candidate.exists():
        return candidate

    matches = list(WINDOWS_DIR.rglob(window_file))
    if matches:
        return matches[0]

    raise FileNotFoundError(f"Janela não encontrada: {window_file}")


def normalize_signal(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float32)
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)

    mean = np.mean(x)
    std = np.std(x)

    if std < 1e-8:
        return x - mean

    return (x - mean) / std


def fix_length(x: np.ndarray, target_len: int) -> np.ndarray:
    if len(x) == target_len:
        return x.astype(np.float32)

    if len(x) > target_len:
        return x[:target_len].astype(np.float32)

    out = np.zeros(target_len, dtype=np.float32)
    out[:len(x)] = x
    return out


def main():
    print("[STEP 1] Loading arrhythmia dataset...")
    df = pd.read_csv(ARR_FILE)

    print(f"[INFO] Input shape: {df.shape}")

    required_cols = ["record_name", "window_file", "arrhythmia_label"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # tamanho alvo baseado no maior comum do dataset
    if "num_samples_record" in df.columns and "sampling_rate" in df.columns:
        # não usamos isso diretamente; janelas já têm tamanho próprio
        pass

    X_list = []
    y_rows = []

    target_len = None
    total = len(df)

    for i, row in df.iterrows():
        window_file = str(row["window_file"]).strip()
        label = str(row["arrhythmia_label"]).strip()
        record_name = str(row["record_name"]).strip()
        base_record = str(row["base_record"]).strip() if "base_record" in df.columns else record_name

        try:
            window_path = locate_window_csv(window_file)
            wdf = pd.read_csv(window_path)
            sig_col = choose_signal_column(wdf)
            signal = wdf[sig_col].values.astype(np.float32)
            signal = normalize_signal(signal)

            if target_len is None:
                target_len = len(signal)

            signal = fix_length(signal, target_len)

            X_list.append(signal)
            y_rows.append({
                "record_name": record_name,
                "base_record": base_record,
                "window_file": window_file,
                "arrhythmia_label": label,
            })

        except Exception:
            # ignora janelas problemáticas
            continue

        if (i + 1) % 500 == 0 or (i + 1) == total:
            print(f"[INFO] Processed {i+1}/{total}")

    if not X_list:
        raise ValueError("Nenhuma janela válida encontrada para a CNN.")

    X = np.stack(X_list).astype(np.float32)
    y_df = pd.DataFrame(y_rows)

    print(f"[INFO] Final X shape: {X.shape}")
    print(f"[INFO] Final y shape: {y_df.shape}")
    print("[INFO] Target distribution:")
    print(y_df["arrhythmia_label"].value_counts())

    OUTPUT_X.parent.mkdir(parents=True, exist_ok=True)
    np.save(OUTPUT_X, X)
    y_df.to_csv(OUTPUT_Y, index=False)

    print(f"[OK] Saved X to: {OUTPUT_X}")
    print(f"[OK] Saved y to: {OUTPUT_Y}")


if __name__ == "__main__":
    main()