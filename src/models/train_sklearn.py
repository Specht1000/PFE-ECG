from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from src.config import PROCESSED_DIR, TRAINED_MODELS_DIR, ensure_directories


def train_random_forest(
    input_file: Path = None,
    model_name: str = "random_forest_rr.pkl"
) -> Path:
    ensure_directories()

    if input_file is None:
        input_file = PROCESSED_DIR / "rr_features_labeled.csv"

    if not input_file.exists():
        raise FileNotFoundError(f"Input dataset not found: {input_file}")

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

    # remove rows with NaN
    valid_mask = ~X.isna().any(axis=1)
    X = X[valid_mask]
    y = y[valid_mask]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced"
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    print("[INFO] Training completed.")
    print(f"[INFO] Dataset used: {input_file}")
    print(f"[INFO] Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print("\n[INFO] Classification report:")
    print(classification_report(y_test, y_pred))
    print("\n[INFO] Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))

    output_file = TRAINED_MODELS_DIR / model_name
    joblib.dump(model, output_file)

    print(f"\n[INFO] Model saved to: {output_file}")

    return output_file


if __name__ == "__main__":
    train_random_forest()