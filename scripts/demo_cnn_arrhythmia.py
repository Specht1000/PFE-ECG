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


# Classes do modelo final forte
# O script final filtrou para:
# normal, supraventricular, ventricular
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

    # manter somente as classes usadas no modelo final
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
    x = x[np.newaxis, :, np.newaxis]  # (1, len, 1)

    probs = model.predict(x, verbose=0)[0]
    pred_idx = int(np.argmax(probs))
    pred_label = CLASS_NAMES[pred_idx]
    confidence = float(probs[pred_idx])

    return pred_label, confidence, probs


def print_result(meta_row, pred_label, confidence, probs):
    true_label = str(meta_row["arrhythmia_label"])
    record_name = str(meta_row["record_name"])
    base_record = str(meta_row["base_record"]) if "base_record" in meta_row else record_name
    window_file = str(meta_row["window_file"])

    print("\n" + "=" * 50)
    print("ECG ARRHYTHMIA DEMO RESULT")
    print("=" * 50)
    print(f"Record name       : {record_name}")
    print(f"Base record       : {base_record}")
    print(f"Window file       : {window_file}")
    print(f"True class        : {true_label}")
    print(f"Predicted class   : {pred_label}")
    print(f"Confidence        : {confidence:.4f}")
    print("-" * 50)
    print("Class probabilities:")
    for cls, p in zip(CLASS_NAMES, probs):
        print(f"  - {cls:16s}: {p:.4f}")
    print("=" * 50 + "\n")


def plot_signal(signal, meta_row, pred_label, confidence, save_path=None):
    true_label = str(meta_row["arrhythmia_label"])
    title = (
        f"ECG Window Analysis\n"
        f"Record: {meta_row['record_name']} | "
        f"True: {true_label} | Pred: {pred_label} ({confidence:.2%})"
    )

    plt.figure(figsize=(12, 4))
    plt.plot(signal)
    plt.title(title)
    plt.xlabel("Samples")
    plt.ylabel("Normalized amplitude")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    if save_path is not None:
        plt.savefig(save_path, dpi=150)
        print(f"[OK] Figure saved to: {save_path}")

    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Demo final de classificação de arritmia com CNN"
    )
    parser.add_argument("--record_name", type=str, default=None, help="Ex.: 100 ou 220")
    parser.add_argument("--window_file", type=str, default=None, help="Ex.: 100_window_0003.csv")
    parser.add_argument("--sample_index", type=int, default=None, help="Índice direto da amostra")
    parser.add_argument("--save_fig", type=str, default=None, help="Caminho para salvar o gráfico PNG")
    args = parser.parse_args()

    print("[STEP 1] Loading assets...")
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

    print("[STEP 4] Plotting signal...")
    plot_signal(signal, meta_row, pred_label, confidence, save_path=args.save_fig)


if __name__ == "__main__":
    main()