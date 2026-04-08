from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from src.config import PROCESSED_DIR, TRAINED_MODELS_DIR, ensure_directories


DROP_COLUMNS = [
    "label",
    "record_name",
    "base_record",
    "window_file",
    "signal_column_used",
    "available_signals",
    "comments",
]


def load_dataset(file_path: Path):
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset not found: {file_path}")

    df = pd.read_csv(file_path)

    if "label" not in df.columns:
        raise ValueError(f"Dataset must contain 'label': {file_path}")

    X = df.drop(columns=DROP_COLUMNS, errors="ignore")
    y = df["label"]

    valid_mask = ~X.isna().any(axis=1)
    X = X[valid_mask]
    y = y[valid_mask]

    return X, y


def train_random_forest_by_group(
    train_file: Path = None,
    test_file: Path = None,
    model_name: str = "random_forest_rr_by_group.pkl"
) -> Path:
    ensure_directories()

    if train_file is None:
        train_file = PROCESSED_DIR / "rr_train_grouped.csv"

    if test_file is None:
        test_file = PROCESSED_DIR / "rr_test_grouped.csv"

    X_train, y_train = load_dataset(train_file)
    X_test, y_test = load_dataset(test_file)

    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced"
    )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print("[INFO] Training completed.")
    print(f"[INFO] Train file: {train_file}")
    print(f"[INFO] Test file: {test_file}")
    print(f"[INFO] Train samples: {len(X_train)}")
    print(f"[INFO] Test samples: {len(X_test)}")
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
    train_random_forest_by_group()