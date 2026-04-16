import pandas as pd
import numpy as np

from src.signal_processing.pan_tompkins import detect_r_peaks, compute_rr_intervals


FS = 250


def run_test(file_path: str):
    print(f"\n=== Testing: {file_path} ===")

    df = pd.read_csv(file_path)
    signal = df["adc_code"].values.astype(float)

    signal = signal - np.mean(signal)

    result = detect_r_peaks(signal, fs=FS)
    r_peaks = result["r_peaks"]

    print(f"Detected R peaks: {len(r_peaks)}")

    rr_intervals_s = compute_rr_intervals(r_peaks, fs=FS)

    if len(rr_intervals_s) > 0:
        bpm_values = 60.0 / rr_intervals_s
        bpm_mean = float(np.mean(bpm_values))
        rr_mean = float(np.mean(rr_intervals_s))
        rr_std = float(np.std(rr_intervals_s, ddof=1)) if len(rr_intervals_s) > 1 else 0.0

        print(f"Mean BPM: {bpm_mean:.2f}")
        print(f"Mean RR: {rr_mean:.4f} s")
        print(f"RR std:  {rr_std:.4f} s")
    else:
        print("Not enough peaks to compute RR intervals.")


if __name__ == "__main__":
    files = [
        "data/synthetic_ads1115/synthetic_normal_1.csv",
        "data/synthetic_ads1115/synthetic_bradycardia_2.csv",
        "data/synthetic_ads1115/synthetic_tachycardia_3.csv",
        "data/synthetic_ads1115/synthetic_possible_af_4.csv",
    ]

    for file_path in files:
        run_test(file_path)