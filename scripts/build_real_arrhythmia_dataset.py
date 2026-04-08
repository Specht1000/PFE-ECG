from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "rr_atr_training_dataset.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "rr_atr_arrhythmia_dataset.csv"


def derive_arrhythmia_label(row) -> str:
    """
    Define a classe da janela com prioridade clínica simples:
    ventricular > supraventricular > fusion > other > normal

    A lógica é:
    - se existir ao menos um batimento ventricular na janela -> ventricular
    - senão, se existir ao menos um supraventricular -> supraventricular
    - senão, se existir ao menos um fusion -> fusion
    - senão, se existir other/unknown -> other
    - caso contrário -> normal
    """
    v = int(row.get("atr_num_ventricular", 0))
    s = int(row.get("atr_num_supraventricular", 0))
    f = int(row.get("atr_num_fusion", 0))
    o = int(row.get("atr_num_other", 0))
    u = int(row.get("atr_num_unknown", 0))
    n = int(row.get("atr_num_normal", 0))
    total = int(row.get("atr_num_annotations", 0))

    if total <= 0:
        return "unlabeled"

    if v > 0:
        return "ventricular"
    if s > 0:
        return "supraventricular"
    if f > 0:
        return "fusion"
    if (o + u) > 0 and n == 0:
        return "other"
    if n > 0:
        return "normal"

    return "other"


def main():
    print("[STEP 1] Loading RR+ATR dataset...")
    df = pd.read_csv(INPUT_FILE)

    print(f"[INFO] Input shape: {df.shape}")
    print(f"[INFO] Input file: {INPUT_FILE}")

    required_cols = [
        "atr_num_annotations",
        "atr_num_normal",
        "atr_num_supraventricular",
        "atr_num_ventricular",
        "atr_num_fusion",
        "atr_num_other",
        "atr_num_unknown",
    ]

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required ATR columns: {missing}")

    print("[STEP 2] Deriving arrhythmia target...")
    df["arrhythmia_label"] = df.apply(derive_arrhythmia_label, axis=1)

    # remove janelas sem anotação útil
    before = len(df)
    df = df[df["arrhythmia_label"] != "unlabeled"].copy()
    after = len(df)

    print(f"[INFO] Removed unlabeled rows: {before - after}")
    print("[INFO] Class distribution:")
    print(df["arrhythmia_label"].value_counts(dropna=False))

    print("[STEP 3] Saving dataset...")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"[OK] Saved: {OUTPUT_FILE}")
    print(f"[INFO] Final shape: {df.shape}")


if __name__ == "__main__":
    main()