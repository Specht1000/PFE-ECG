from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.simulation.ecg_generator import generate_clean_ecg
from src.simulation.analog_chain import apply_analog_chain
from src.simulation.ads1115_emulator import emulate_ads1115


@dataclass
class SyntheticADS1115Config:
    label: str = "normal"
    duration_s: float = 30.0
    sampling_rate_hz: int = 250

    ads1115_full_scale_v: float = 4.096
    ads1115_mode: str = "single_ended"
    differential_midpoint_v: float = 1.5

    analog_gain: float = 1.0
    analog_offset_v: float = 1.5

    baseline_wander_amp_v: float = 0.03
    baseline_wander_freq_hz: float = 0.33

    mains_amp_v: float = 0.004
    mains_freq_hz: float = 50.0

    white_noise_std_v: float = 0.003
    muscle_noise_std_v: float = 0.002

    saturation_min_v: float = 0.0
    saturation_max_v: float = 3.3

    seed: int | None = 42


def build_synthetic_ads1115_record(config: SyntheticADS1115Config) -> pd.DataFrame:
    clean = generate_clean_ecg(
        label=config.label,
        duration_s=config.duration_s,
        sampling_rate_hz=config.sampling_rate_hz,
        seed=config.seed,
    )

    t = clean["t"]
    ecg_clean_mv = clean["ecg_clean"] * 1000.0

    analog_v = apply_analog_chain(
        ecg_clean_mv=ecg_clean_mv,
        t=t,
        analog_gain=config.analog_gain,
        analog_offset_v=config.analog_offset_v,
        baseline_wander_amp_v=config.baseline_wander_amp_v,
        baseline_wander_freq_hz=config.baseline_wander_freq_hz,
        mains_amp_v=config.mains_amp_v,
        mains_freq_hz=config.mains_freq_hz,
        white_noise_std_v=config.white_noise_std_v,
        muscle_noise_std_v=config.muscle_noise_std_v,
        saturation_min_v=config.saturation_min_v,
        saturation_max_v=config.saturation_max_v,
        seed=config.seed,
    )

    adc_code = emulate_ads1115(
        analog_v=analog_v,
        full_scale_v=config.ads1115_full_scale_v,
        mode=config.ads1115_mode,
        v_ref_mid=config.differential_midpoint_v,
    )

    df = pd.DataFrame({
        "sample_index": np.arange(len(t), dtype=np.int32),
        "timestamp_s": t,
        "ecg_clean_mv": ecg_clean_mv,
        "analog_v": analog_v,
        "adc_code": adc_code,
        "label": config.label,
        "source": "synthetic_ads1115",
    })

    return df


def save_record(
    df: pd.DataFrame,
    config: SyntheticADS1115Config,
    output_dir: str | Path,
    stem: str,
) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / f"{stem}.csv"
    json_path = output_dir / f"{stem}_config.json"

    df.to_csv(csv_path, index=False)

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(asdict(config), f, indent=2, ensure_ascii=False)