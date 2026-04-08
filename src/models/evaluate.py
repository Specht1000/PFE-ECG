from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from src.config import PROCESSED_DIR, TRAINED_MODELS_DIR


def evaluate_model(
    model_file: Path = None,
    input_file: Path = None
) -> None:
    """
    Load a trained model and evaluate it on the labeled dataset.
    """
    if model_file is None:
        model_file = TRAINED_MODELS_DIR / "random_forest.pkl"

    if input_file is None:
        input_file = PROCESSED_DIR / "features_labeled.csv"

    if not model_file.exists():
        raise FileNotFoundError(f"Model file not found: {model_file}")

    if not input_file.exists():
        raise FileNotFoundError(f"Dataset file not found: {input_file}")

    model = joblib.load(model_file)
    df = pd.read_csv(input_file)

    if "label" not in df.columns:
        raise ValueError("The dataset must contain a 'label' column.")

    drop_columns = [
        "label",
        "record_name",
        "window_file",
        "signal_column_used",
        "available_signals",
        "comments",
    ]

    X = df.drop(columns=drop_columns, errors="ignore")
    y = df["label"]

    y_pred = model.predict(X)

    print(f"[INFO] Accuracy: {accuracy_score(y, y_pred):.4f}")
    print("\n[INFO] Classification report:")
    print(classification_report(y, y_pred))
    print("\n[INFO] Confusion matrix:")
    print(confusion_matrix(y, y_pred))


if __name__ == "__main__":
    evaluate_model()