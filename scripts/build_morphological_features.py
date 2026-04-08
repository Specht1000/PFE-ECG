from pathlib import Path
import re

import numpy as np
import pandas as pd
from scipy.signal import find_peaks


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WINDOWS_DIR = PROJECT_ROOT / "data" / "interim" / "windows"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RR_FILE = PROCESSED_DIR / "rr_atr_training_dataset.csv"
OUTPUT_FILE = PROCESSED_DIR / "ecg_morphological_features.csv"


def choose_signal_column(df: pd.DataFrame) -> str:
    preferred = ["MLII", "V5", "V1", "ECG", "signal", "value"]
    for col in preferred:
        if col in df.columns:
            return col

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        raise ValueError("Nenhuma coluna numérica encontrada na janela.")
    return numeric_cols[0]


def estimate_qrs_features(signal: np.ndarray, fs: float):
    signal = np.asarray(signal, dtype=float)

    if len(signal) < 5:
        return {
            "morph_num_peaks": 0,
            "morph_r_mean": 0.0,
            "morph_r_std": 0.0,
            "morph_r_max": 0.0,
            "morph_r_min": 0.0,
            "morph_peak_to_peak_mean": 0.0,
            "morph_qrs_width_mean": 0.0,
            "morph_qrs_width_std": 0.0,
            "morph_slope_mean": 0.0,
            "morph_slope_std": 0.0,
            "morph_local_energy_mean": 0.0,
            "morph_local_energy_std": 0.0,
        }

    # normalização simples
    x = signal - np.mean(signal)
    std = np.std(x)
    if std > 0:
        x = x / std

    # detecção aproximada de picos R
    distance = max(1, int(0.2 * fs))  # ~200 ms
    prominence = 0.5
    peaks, props = find_peaks(x, distance=distance, prominence=prominence)

    if len(peaks) == 0:
        return {
            "morph_num_peaks": 0,
            "morph_r_mean": 0.0,
            "morph_r_std": 0.0,
            "morph_r_max": 0.0,
            "morph_r_min": 0.0,
            "morph_peak_to_peak_mean": 0.0,
            "morph_qrs_width_mean": 0.0,
            "morph_qrs_width_std": 0.0,
            "morph_slope_mean": 0.0,
            "morph_slope_std": 0.0,
            "morph_local_energy_mean": 0.0,
            "morph_local_energy_std": 0.0,
        }

    r_vals = x[peaks]

    # largura aproximada do QRS pela largura a meia altura
    widths = []
    slopes = []
    local_energies = []
    half_window = max(1, int(0.08 * fs))  # ~80 ms de cada lado

    dx = np.diff(x, prepend=x[0])

    for p in peaks:
        left = max(0, p - half_window)
        right = min(len(x), p + half_window + 1)

        segment = x[left:right]
        dsegment = dx[left:right]

        if len(segment) > 0:
            local_energies.append(float(np.sum(segment ** 2)))
            slopes.append(float(np.max(np.abs(dsegment))))

            peak_amp = x[p]
            half_amp = peak_amp * 0.5

            l = p
            while l > 0 and x[l] > half_amp:
                l -= 1

            r = p
            while r < len(x) - 1 and x[r] > half_amp:
                r += 1

            widths.append((r - l) / fs)

    peak_to_peak = np.diff(peaks) / fs if len(peaks) > 1 else np.array([0.0])

    return {
        "morph_num_peaks": int(len(peaks)),
        "morph_r_mean": float(np.mean(r_vals)),
        "morph_r_std": float(np.std(r_vals)),
        "morph_r_max": float(np.max(r_vals)),
        "morph_r_min": float(np.min(r_vals)),
        "morph_peak_to_peak_mean": float(np.mean(peak_to_peak)),
        "morph_qrs_width_mean": float(np.mean(widths)) if widths else 0.0,
        "morph_qrs_width_std": float(np.std(widths)) if widths else 0.0,
        "morph_slope_mean": float(np.mean(slopes)) if slopes else 0.0,
        "morph_slope_std": float(np.std(slopes)) if slopes else 0.0,
        "morph_local_energy_mean": float(np.mean(local_energies)) if local_energies else 0.0,
        "morph_local_energy_std": float(np.std(local_energies)) if local_energies else 0.0,
    }


def parse_window_index(window_file: str) -> int:
    stem = Path(window_file).stem
    m = re.search(r"_window_(\d+)$", stem)
    if not m:
        raise ValueError(f"Formato inesperado de window_file: {window_file}")
    return int(m.group(1))


def locate_window_csv(record_name: str, window_file: str) -> Path:
    candidate = WINDOWS_DIR / window_file
    if candidate.exists():
        return candidate

    # fallback recursivo
    matches = list(WINDOWS_DIR.rglob(window_file))
    if matches:
        return matches[0]

    raise FileNotFoundError(f"Janela não encontrada: {window_file}")


def main():
    print("[STEP 1] Loading RR+ATR dataset...")
    rr_df = pd.read_csv(RR_FILE)

    if rr_df.empty:
        raise ValueError("RR+ATR dataset está vazio.")

    required_cols = ["record_name", "window_file", "sampling_rate"]
    missing = [c for c in required_cols if c not in rr_df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes em rr_atr_training_dataset.csv: {missing}")

    print(f"[INFO] Input rows: {len(rr_df)}")

    rows = []
    total = len(rr_df)

    for i, row in rr_df.iterrows():
        record_name = str(row["record_name"]).strip()
        window_file = str(row["window_file"]).strip()
        fs = float(row["sampling_rate"])

        try:
            window_path = locate_window_csv(record_name, window_file)
            wdf = pd.read_csv(window_path)
            sig_col = choose_signal_column(wdf)
            signal = wdf[sig_col].values

            feats = estimate_qrs_features(signal, fs)
            feats["record_name"] = record_name
            feats["window_file"] = window_file
            rows.append(feats)

        except Exception:
            rows.append({
                "record_name": record_name,
                "window_file": window_file,
                "morph_num_peaks": 0,
                "morph_r_mean": 0.0,
                "morph_r_std": 0.0,
                "morph_r_max": 0.0,
                "morph_r_min": 0.0,
                "morph_peak_to_peak_mean": 0.0,
                "morph_qrs_width_mean": 0.0,
                "morph_qrs_width_std": 0.0,
                "morph_slope_mean": 0.0,
                "morph_slope_std": 0.0,
                "morph_local_energy_mean": 0.0,
                "morph_local_energy_std": 0.0,
            })

        if (i + 1) % 500 == 0 or (i + 1) == total:
            print(f"[INFO] Processed {i+1}/{total}")

    out_df = pd.DataFrame(rows).drop_duplicates(subset=["record_name", "window_file"])
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUTPUT_FILE, index=False)

    print(f"[OK] Saved morphological features to: {OUTPUT_FILE}")
    print(f"[INFO] Output shape: {out_df.shape}")


if __name__ == "__main__":
    main()