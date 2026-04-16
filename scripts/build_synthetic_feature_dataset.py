import numpy as np
import pandas as pd
from pathlib import Path

from src.simulation.ecg_generator import generate_rr_intervals


def compute_features(rr_s):
    rr_s = np.array(rr_s)

    hr = 60.0 / rr_s

    features = {
        "rr_mean": np.mean(rr_s),
        "rr_std": np.std(rr_s, ddof=1),
        "rr_min": np.min(rr_s),
        "rr_max": np.max(rr_s),
        "rr_cv": np.std(rr_s, ddof=1) / np.mean(rr_s),

        "hr_mean_bpm": np.mean(hr),
        "hr_std_bpm": np.std(hr, ddof=1),

        "num_r_peaks": len(rr_s) + 1,
        "num_rr_intervals": len(rr_s),
    }

    return features


def generate_samples(label, n_samples, seed_base=0):
    rows = []

    for i in range(n_samples):
        seed = seed_base + i

        rr = generate_rr_intervals(
            duration_s=10.0,
            label=label,
            rng=np.random.default_rng(seed)
        )

        # pega janela menor
        if len(rr) > 8:
            rr = rr[:8]

        feat = compute_features(rr)
        feat["label"] = label
        feat["source"] = "synthetic"

        rows.append(feat)

    return rows


def main():
    output_path = Path("data/processed/synthetic_features.csv")

    dataset = []

    dataset += generate_samples("bradycardia", 600, 1000)
    dataset += generate_samples("tachycardia", 1600, 2000)
    dataset += generate_samples("possible_af", 800, 3000)
    dataset += generate_samples("normal", 100, 4000)

    df = pd.DataFrame(dataset)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print("Saved:", output_path)
    print(df.head())


if __name__ == "__main__":
    main()