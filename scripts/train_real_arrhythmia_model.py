from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import LabelEncoder, StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "processed" / "rr_atr_arrhythmia_dataset.csv"


def main():
    print("[STEP 1] Loading dataset...")
    df = pd.read_csv(DATA_FILE)

    print(f"[INFO] Shape: {df.shape}")
    print(f"[INFO] File: {DATA_FILE}")

    target_col = "arrhythmia_label"
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found.")

    # split por grupo/registro
    if "base_record" in df.columns:
        groups = df["base_record"].astype(str)
    elif "record_name" in df.columns:
        groups = df["record_name"].astype(str)
    else:
        raise ValueError("Neither 'base_record' nor 'record_name' found for grouped split.")

    print("[INFO] Target distribution:")
    print(df[target_col].value_counts(dropna=False))

    # remover colunas que causam vazamento
    drop_cols = [
        target_col,
        "record_name",
        "window_file",
        "available_signals",
        "comments",
        "record_path",
        "source_file",
        "__source_rr_file",
        "signal_column_used",
        "base_record",
        "window_index",
        "label",  # remove o alvo antigo
    ]

    # remover TODAS as colunas ATR usadas para construir o alvo
    atr_cols = [c for c in df.columns if c.startswith("atr_")]
    drop_cols.extend(atr_cols)

    X = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore").copy()
    y = df[target_col].copy()

    # manter só colunas numéricas
    non_numeric_cols = X.select_dtypes(exclude=[np.number]).columns.tolist()
    if non_numeric_cols:
        print(f"[INFO] Removing non-numeric columns: {non_numeric_cols}")
        X = X.drop(columns=non_numeric_cols)

    X = X.replace([np.inf, -np.inf], np.nan).fillna(0)

    print(f"[INFO] Feature columns ({len(X.columns)}): {X.columns.tolist()}")

    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    print("[INFO] Classes:", list(le.classes_))

    # split por registros
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(gss.split(X, y_encoded, groups=groups))

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]
    y_train = y_encoded[train_idx]
    y_test = y_encoded[test_idx]

    print("[INFO] Train shape:", X_train.shape)
    print("[INFO] Test shape:", X_test.shape)
    print("[INFO] Train groups:", len(set(groups.iloc[train_idx])))
    print("[INFO] Test groups:", len(set(groups.iloc[test_idx])))

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    print("[STEP 2] Training model...")
    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced_subsample",
    )
    model.fit(X_train, y_train)

    print("[STEP 3] Evaluating...")
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    print(f"\n=== ACCURACY ===\n{acc:.4f}")

    print("\n=== CLASSIFICATION REPORT ===")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    print("\n=== CONFUSION MATRIX ===")
    print(confusion_matrix(y_test, y_pred))

    # importância das features
    feature_importance = pd.DataFrame({
        "feature": X.columns,
        "importance": model.feature_importances_
    }).sort_values("importance", ascending=False)

    out_file = PROJECT_ROOT / "data" / "processed" / "real_arrhythmia_feature_importance.csv"
    feature_importance.to_csv(out_file, index=False)

    print("\n=== TOP 15 FEATURES ===")
    print(feature_importance.head(15).to_string(index=False))
    print(f"\n[OK] Feature importance saved to: {out_file}")


if __name__ == "__main__":
    main()