from __future__ import annotations

import numpy as np


def apply_analog_chain(
    ecg_clean_mv: np.ndarray,
    t: np.ndarray,
    analog_gain: float = 1.0,
    analog_offset_v: float = 1.5,
    baseline_wander_amp_v: float = 0.03,
    baseline_wander_freq_hz: float = 0.33,
    mains_amp_v: float = 0.004,
    mains_freq_hz: float = 50.0,
    white_noise_std_v: float = 0.003,
    muscle_noise_std_v: float = 0.002,
    saturation_min_v: float = 0.0,
    saturation_max_v: float = 3.3,
    seed: int | None = None,
) -> np.ndarray:
    rng = np.random.default_rng(seed)

    ecg_v = (ecg_clean_mv / 1000.0) * analog_gain

    baseline = baseline_wander_amp_v * np.sin(2.0 * np.pi * baseline_wander_freq_hz * t)
    mains = mains_amp_v * np.sin(2.0 * np.pi * mains_freq_hz * t)
    white = rng.normal(0.0, white_noise_std_v, size=t.shape)
    muscle = rng.normal(0.0, muscle_noise_std_v, size=t.shape)

    analog_v = analog_offset_v + ecg_v + baseline + mains + white + muscle
    analog_v = np.clip(analog_v, saturation_min_v, saturation_max_v)

    return analog_v