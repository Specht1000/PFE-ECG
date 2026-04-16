from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

FEATURE_COLUMNS: List[str] = [
    "rr_mean",
    "rr_std",
    "rr_min",
    "rr_max",
    "rr_cv",
    "hr_mean_bpm",
    "hr_std_bpm",
    "num_r_peaks",
    "num_rr_intervals",
]

LABEL_COLUMN = "label"


def load_xy(csv_path: str):
    df = pd.read_csv(csv_path)

    missing = [c for c in FEATURE_COLUMNS + [LABEL_COLUMN] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in {csv_path}: {missing}")

    X = df[FEATURE_COLUMNS].copy()
    y = df[LABEL_COLUMN].astype(str).copy()
    return X, y


def train_and_evaluate(train_csv: str, test_csv: str, title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    X_train, y_train = load_xy(train_csv)
    X_test, y_test = load_xy(test_csv)

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {acc:.4f}\n")

    print("Classification report:")
    print(classification_report(y_test, y_pred, digits=4, zero_division=0))

    print("Confusion matrix:")
    cm = confusion_matrix(y_test, y_pred, labels=sorted(y_test.unique()))
    cm_df = pd.DataFrame(cm, index=sorted(y_test.unique()), columns=sorted(y_test.unique()))
    print(cm_df)

    return model


def main():
    real_train = "data/processed/rr_train_grouped.csv"
    augmented_train = "data/processed/rr_train_augmented.csv"
    real_test = "data/processed/rr_test_grouped.csv"

    train_and_evaluate(
        train_csv=real_train,
        test_csv=real_test,
        title="MODEL A - TRAIN ONLY WITH REAL DATA",
    )

    train_and_evaluate(
        train_csv=augmented_train,
        test_csv=real_test,
        title="MODEL B - TRAIN WITH REAL + SYNTHETIC DATA",
    )


if __name__ == "__main__":
    main()