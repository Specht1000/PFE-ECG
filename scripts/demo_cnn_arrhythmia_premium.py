from pathlib import Path
import argparse
import random

import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

X_FILE = PROCESSED_DIR / "cnn_X.npy"
Y_FILE = PROCESSED_DIR / "cnn_y.csv"
MODEL_FILE = PROCESSED_DIR / "cnn_arrhythmia_model_final.keras"

CLASS_NAMES = ["normal", "supraventricular", "ventricular"]


def load_assets():
    if not X_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {X_FILE}")
    if not Y_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {Y_FILE}")
    if not MODEL_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {MODEL_FILE}")

    X = np.load(X_FILE)
    y_df = pd.read_csv(Y_FILE)

    keep = y_df["arrhythmia_label"].astype(str).isin(CLASS_NAMES).values
    X = X[keep]
    y_df = y_df.loc[keep].reset_index(drop=True)

    model = tf.keras.models.load_model(MODEL_FILE, compile=False)
    return X, y_df, model


def normalize_per_window(signal: np.ndarray) -> np.ndarray:
    signal = signal.astype(np.float32)
    mean = np.mean(signal)
    std = np.std(signal)
    return (signal - mean) / (std + 1e-8)


def choose_sample(y_df: pd.DataFrame, record_name=None, window_file=None, sample_index=None):
    if sample_index is not None:
        if sample_index < 0 or sample_index >= len(y_df):
            raise IndexError(f"sample_index fora do intervalo: {sample_index}")
        return sample_index

    if window_file is not None:
        matches = y_df.index[y_df["window_file"].astype(str) == str(window_file)].tolist()
        if not matches:
            raise ValueError(f"Nenhuma janela encontrada com window_file='{window_file}'")
        return matches[0]

    if record_name is not None:
        matches = y_df.index[y_df["record_name"].astype(str) == str(record_name)].tolist()
        if not matches:
            raise ValueError(f"Nenhum registro encontrado com record_name='{record_name}'")
        return random.choice(matches)

    return random.randint(0, len(y_df) - 1)


def predict_sample(model, signal_1d: np.ndarray):
    x = normalize_per_window(signal_1d)
    x = x[np.newaxis, :, np.newaxis]

    probs = model.predict(x, verbose=0)[0]
    pred_idx = int(np.argmax(probs))
    pred_label = CLASS_NAMES[pred_idx]
    confidence = float(probs[pred_idx])

    return pred_label, confidence, probs


def risk_level(pred_label: str, confidence: float) -> str:
    if pred_label == "normal":
        if confidence >= 0.85:
            return "LOW"
        return "MODERATE"

    if confidence >= 0.85:
        return "HIGH"
    if confidence >= 0.65:
        return "MODERATE"
    return "LOW"


def recommendation(pred_label: str, confidence: float) -> str:
    if pred_label == "normal":
        if confidence >= 0.85:
            return "No abnormal rhythm pattern detected in this ECG window."
        return "Rhythm appears normal, but confidence is moderate."

    if pred_label == "ventricular":
        return "Possible ventricular arrhythmia pattern detected. Clinical review recommended."

    if pred_label == "supraventricular":
        return "Possible supraventricular arrhythmia pattern detected. Further analysis recommended."

    return "ECG pattern requires additional evaluation."


def alert_color(pred_label: str):
    if pred_label == "normal":
        return "#2e7d32"
    if pred_label == "supraventricular":
        return "#ef6c00"
    if pred_label == "ventricular":
        return "#c62828"
    return "#455a64"


def print_result(meta_row, pred_label, confidence, probs):
    true_label = str(meta_row["arrhythmia_label"])
    record_name = str(meta_row["record_name"])
    base_record = str(meta_row["base_record"]) if "base_record" in meta_row else record_name
    window_file = str(meta_row["window_file"])

    level = risk_level(pred_label, confidence)
    rec = recommendation(pred_label, confidence)

    print("\n" + "=" * 60)
    print("PREMIUM ECG ARRHYTHMIA ANALYSIS")
    print("=" * 60)
    print(f"Record name         : {record_name}")
    print(f"Base record         : {base_record}")
    print(f"Window file         : {window_file}")
    print(f"True class          : {true_label}")
    print(f"Predicted class     : {pred_label}")
    print(f"Confidence          : {confidence:.4f}")
    print(f"Alert level         : {level}")
    print("-" * 60)
    print("Class probabilities:")
    for cls, p in zip(CLASS_NAMES, probs):
        print(f"  - {cls:16s}: {p:.4f}")
    print("-" * 60)
    print(f"Recommendation      : {rec}")
    print("=" * 60 + "\n")


def plot_premium_dashboard(signal, meta_row, pred_label, confidence, probs, save_path=None):
    true_label = str(meta_row["arrhythmia_label"])
    rec = recommendation(pred_label, confidence)
    level = risk_level(pred_label, confidence)
    color = alert_color(pred_label)

    fig = plt.figure(figsize=(14, 8))
    gs = fig.add_gridspec(3, 1, height_ratios=[0.9, 2.2, 1.4])

    # Header / status
    ax0 = fig.add_subplot(gs[0])
    ax0.axis("off")
    ax0.set_facecolor("#f5f5f5")

    status_text = (
        "ECG ARRHYTHMIA ANALYSIS DASHBOARD\n"
        f"Record: {meta_row['record_name']}   |   Window: {meta_row['window_file']}\n"
        f"True: {true_label}   |   Predicted: {pred_label}   |   Confidence: {confidence:.2%}   |   Alert: {level}"
    )
    ax0.text(
        0.5, 0.62, status_text,
        ha="center", va="center",
        fontsize=16, fontweight="bold", color="#222222"
    )

    ax0.text(
        0.5, 0.18, rec,
        ha="center", va="center",
        fontsize=12, color=color,
        bbox=dict(boxstyle="round,pad=0.35", facecolor="#ffffff", edgecolor=color, linewidth=2)
    )

    # ECG signal
    ax1 = fig.add_subplot(gs[1])
    ax1.plot(signal, linewidth=1.6)
    ax1.set_title("ECG Signal Window", fontsize=14, fontweight="bold")
    ax1.set_xlabel("Samples")
    ax1.set_ylabel("Normalized amplitude")
    ax1.grid(True, alpha=0.3)

    # Probability bars
    ax2 = fig.add_subplot(gs[2])
    bars = ax2.bar(CLASS_NAMES, probs, edgecolor="black")
    for bar, cls in zip(bars, CLASS_NAMES):
        if cls == pred_label:
            bar.set_linewidth(2.5)
            bar.set_edgecolor(color)

    ax2.set_ylim(0, 1.0)
    ax2.set_title("Prediction Confidence by Class", fontsize=14, fontweight="bold")
    ax2.set_ylabel("Probability")
    ax2.grid(True, axis="y", alpha=0.3)

    for i, p in enumerate(probs):
        ax2.text(i, p + 0.03, f"{p:.2f}", ha="center", va="bottom", fontsize=11)

    plt.tight_layout()

    if save_path is not None:
        save_path = Path(save_path)
        plt.savefig(save_path, dpi=160, bbox_inches="tight")
        print(f"[OK] Premium figure saved to: {save_path}")

    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Premium ECG arrhythmia demo"
    )
    parser.add_argument("--record_name", type=str, default=None, help="Ex.: 100 ou 220")
    parser.add_argument("--window_file", type=str, default=None, help="Ex.: 100_window_0003.csv")
    parser.add_argument("--sample_index", type=int, default=None, help="Índice direto da amostra")
    parser.add_argument("--save_fig", type=str, default=None, help="Salvar dashboard em PNG")
    args = parser.parse_args()

    print("[STEP 1] Loading premium demo assets...")
    X, y_df, model = load_assets()

    print(f"[INFO] X shape: {X.shape}")
    print(f"[INFO] Metadata shape: {y_df.shape}")
    print(f"[INFO] Model loaded: {MODEL_FILE}")

    print("[STEP 2] Selecting sample...")
    idx = choose_sample(
        y_df,
        record_name=args.record_name,
        window_file=args.window_file,
        sample_index=args.sample_index,
    )

    meta_row = y_df.iloc[idx]
    signal = X[idx]

    print(f"[INFO] Selected sample index: {idx}")

    print("[STEP 3] Predicting...")
    pred_label, confidence, probs = predict_sample(model, signal)

    print_result(meta_row, pred_label, confidence, probs)

    print("[STEP 4] Rendering premium dashboard...")
    plot_premium_dashboard(signal, meta_row, pred_label, confidence, probs, save_path=args.save_fig)


if __name__ == "__main__":
    main()