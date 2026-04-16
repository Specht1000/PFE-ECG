from __future__ import annotations

from src.simulation.dataset_builder import (
    SyntheticADS1115Config,
    build_synthetic_ads1115_record,
    save_record,
)


def main() -> None:
    configs = [
        SyntheticADS1115Config(label="normal", seed=1),
        SyntheticADS1115Config(label="bradycardia", seed=2),
        SyntheticADS1115Config(label="tachycardia", seed=3),
        SyntheticADS1115Config(label="possible_af", seed=4),
    ]

    for cfg in configs:
        df = build_synthetic_ads1115_record(cfg)
        stem = f"synthetic_{cfg.label}_{cfg.seed}"
        save_record(df, cfg, "data/synthetic_ads1115", stem)
        print(f"Saved: {stem}")


if __name__ == "__main__":
    main()