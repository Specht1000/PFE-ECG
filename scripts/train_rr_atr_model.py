import pandas as pd
import numpy as np

from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.ensemble import RandomForestClassifier

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "processed" / "rr_atr_training_dataset.csv"


def find_target_column(df):
    for col in ["beat_class", "label", "arrhythmia_class"]:
        if col in df.columns:
            return col
    raise ValueError(f"Nenhuma coluna target encontrada. Colunas: {df.columns.tolist()}")


def main():
    print("[STEP 1] Loading dataset...")
    df = pd.read_csv(DATA_FILE)

    print(f"[INFO] Shape: {df.shape}")
    target_col = find_target_column(df)
    print(f"[INFO] Using target column: {target_col}")

    # manter grupo para split por registro
    if "base_record" in df.columns:
        groups = df["base_record"].astype(str)
    elif "record_name" in df.columns:
        groups = df["record_name"].astype(str)
    else:
        raise ValueError("Nenhuma coluna de grupo encontrada ('base_record' ou 'record_name').")

    # remover colunas com alto risco de vazamento
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
        "base_record",     # evita memorizar o registro
        "window_index",    # pode ajudar a memorizar posição
    ]

    # TESTE HONESTO: remover também todas as ATR, que vêm das anotações
    atr_cols = [c for c in df.columns if c.startswith("atr_")]
    drop_cols.extend(atr_cols)

    X = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore").copy()
    y = df[target_col].copy()

    non_numeric_cols = X.select_dtypes(exclude=[np.number]).columns.tolist()
    if non_numeric_cols:
        print(f"[INFO] Removing non-numeric columns: {non_numeric_cols}")
        X = X.drop(columns=non_numeric_cols)

    X = X.replace([np.inf, -np.inf], np.nan).fillna(0)

    print(f"[INFO] Final feature columns ({len(X.columns)}): {X.columns.tolist()}")

    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    print("[INFO] Classes:", list(le.classes_))

    # split por grupo, não aleatório por linha
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(gss.split(X, y_encoded, groups=groups))

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]
    y_train = y_encoded[train_idx]
    y_test = y_encoded[test_idx]

    print("[INFO] Train:", X_train.shape)
    print("[INFO] Test:", X_test.shape)
    print("[INFO] Train groups:", len(set(groups.iloc[train_idx])))
    print("[INFO] Test groups:", len(set(groups.iloc[test_idx])))

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    print("[STEP 2] Training model...")
    model = RandomForestClassifier(
        n_estimators=150,
        random_state=42,
        n_jobs=-1
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


if __name__ == "__main__":
    main()