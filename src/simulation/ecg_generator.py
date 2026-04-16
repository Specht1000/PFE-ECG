from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class ECGClassConfig:
    label: str
    hr_mean_bpm: float
    hr_std_bpm: float
    rr_irregularity: float
    p_wave: bool = True


CLASS_LIBRARY = {
    "normal": ECGClassConfig("normal", 75.0, 2.0, 0.015, True),
    "bradycardia": ECGClassConfig("bradycardia", 48.0, 2.0, 0.020, True),
    "tachycardia": ECGClassConfig("tachycardia", 125.0, 5.0, 0.025, True),
    "possible_af": ECGClassConfig("possible_af", 95.0, 12.0, 0.140, False),
}


def _gaussian(x: np.ndarray, mu: float, sigma: float, amp: float) -> np.ndarray:
    return amp * np.exp(-0.5 * ((x - mu) / sigma) ** 2)


def generate_rr_intervals(
    duration_s: float,
    label: str,
    rng: np.random.Generator,
) -> np.ndarray:
    if label not in CLASS_LIBRARY:
        raise ValueError(f"Unsupported label: {label}")

    cfg = CLASS_LIBRARY[label]
    rr_list = []
    elapsed = 0.0

    while elapsed < duration_s + 1.0:
        hr = max(25.0, rng.normal(cfg.hr_mean_bpm, cfg.hr_std_bpm))
        rr = 60.0 / hr

        irregular_factor = rng.normal(1.0, cfg.rr_irregularity)
        rr = rr * irregular_factor
        rr = float(np.clip(rr, 0.30, 2.20))

        rr_list.append(rr)
        elapsed += rr

    return np.array(rr_list, dtype=np.float64)


def generate_r_peak_times(rr_intervals_s: np.ndarray) -> np.ndarray:
    return np.cumsum(rr_intervals_s)


def synthesize_ecg_from_rpeaks(
    t: np.ndarray,
    r_peak_times: np.ndarray,
    label: str,
) -> np.ndarray:
    cfg = CLASS_LIBRARY[label]
    signal = np.zeros_like(t, dtype=np.float64)

    for r_t in r_peak_times:
        if cfg.p_wave:
            signal += _gaussian(t, r_t - 0.18, 0.025, 0.08)

        signal += _gaussian(t, r_t - 0.02, 0.008, -0.10)  # Q
        signal += _gaussian(t, r_t, 0.012, 1.00)          # R
        signal += _gaussian(t, r_t + 0.025, 0.010, -0.22) # S
        signal += _gaussian(t, r_t + 0.24, 0.060, 0.30)   # T

    return signal


def generate_clean_ecg(
    label: str,
    duration_s: float,
    sampling_rate_hz: float,
    seed: int | None = None,
) -> dict:
    rng = np.random.default_rng(seed)
    n = int(duration_s * sampling_rate_hz)
    t = np.arange(n, dtype=np.float64) / float(sampling_rate_hz)

    rr_intervals_s = generate_rr_intervals(duration_s, label, rng)
    r_peak_times = generate_r_peak_times(rr_intervals_s)
    r_peak_times = r_peak_times[r_peak_times < duration_s]

    ecg_clean = synthesize_ecg_from_rpeaks(t, r_peak_times, label)

    return {
        "t": t,
        "ecg_clean": ecg_clean,
        "rr_intervals_s": rr_intervals_s,
        "r_peak_times": r_peak_times,
    }