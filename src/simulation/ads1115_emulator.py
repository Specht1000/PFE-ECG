from __future__ import annotations

import numpy as np


ADS1115_FULL_SCALE_OPTIONS = {
    "6.144": 6.144,
    "4.096": 4.096,
    "2.048": 2.048,
    "1.024": 1.024,
    "0.512": 0.512,
    "0.256": 0.256,
}


def emulate_ads1115(
    analog_v: np.ndarray,
    full_scale_v: float = 4.096,
    mode: str = "single_ended",
    v_ref_mid: float = 1.5,
) -> np.ndarray:
    if mode not in {"single_ended", "differential"}:
        raise ValueError("mode must be 'single_ended' or 'differential'")

    if mode == "single_ended":
        measured_v = analog_v
        measured_v = np.clip(measured_v, 0.0, full_scale_v)
        codes = np.round((measured_v / full_scale_v) * 32767.0)
        return codes.astype(np.int16)

    measured_v = analog_v - v_ref_mid
    measured_v = np.clip(measured_v, -full_scale_v, full_scale_v)
    codes = np.round((measured_v / full_scale_v) * 32767.0)
    codes = np.clip(codes, -32768, 32767)
    return codes.astype(np.int16)