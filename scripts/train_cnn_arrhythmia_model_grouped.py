from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_class_weight


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

X_FILE = PROCESSED_DIR / "cnn_X.npy"
Y_FILE = PROCESSED_DIR / "cnn_y.csv"
MODEL_FILE = PROCESSED_DIR / "cnn_arrhythmia_model_grouped.keras"


def build_model(input_length: int, num_classes: int) -> tf.keras.Model:
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(input_length, 1)),

        tf.keras.layers.Conv1D(32, kernel_size=7, padding="same", activation="relu"),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.MaxPooling1D(pool_size=2),

        tf.keras.layers.Conv1D(64, kernel_size=5, padding="same", activation="relu"),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.MaxPooling1D(pool_size=2),

        tf.keras.layers.Conv1D(128, kernel_size=5, padding="same", activation="relu"),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.MaxPooling1D(pool_size=2),

        tf.keras.layers.Conv1D(128, kernel_size=3, padding="same", activation="relu"),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.GlobalAveragePooling1D(),

        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dropout(0.2),

        tf.keras.layers.Dense(num_classes, activation="softmax"),
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def main():
    print("[STEP 1] Loading grouped CNN dataset...")

    if not X_FILE.exists():
        raise FileNotFoundError(f"X file not found: {X_FILE}")
    if not Y_FILE.exists():
        raise FileNotFoundError(f"Y file not found: {Y_FILE}")

    X = np.load(X_FILE)
    y_df = pd.read_csv(Y_FILE)

    print(f"[INFO] X shape: {X.shape}")
    print(f"[INFO] y shape: {y_df.shape}")

    required_cols = ["arrhythmia_label", "base_record"]
    missing = [c for c in required_cols if c not in y_df.columns]
    if missing:
        raise ValueError(f"Missing required columns in y file: {missing}")

    y = y_df["arrhythmia_label"].astype(str).values
    groups = y_df["base_record"].astype(str).values

    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    print("[INFO] Classes:", list(le.classes_))
    print("[INFO] Target distribution:")
    print(pd.Series(y).value_counts())

    # split por grupos
    gss_outer = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    trainval_idx, test_idx = next(gss_outer.split(X, y_encoded, groups=groups))

    X_trainval = X[trainval_idx]
    y_trainval = y_encoded[trainval_idx]
    groups_trainval = groups[trainval_idx]

    X_test = X[test_idx]
    y_test = y_encoded[test_idx]
    groups_test = groups[test_idx]

    # validação também por grupos
    gss_inner = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, val_idx = next(gss_inner.split(X_trainval, y_trainval, groups=groups_trainval))

    X_train = X_trainval[train_idx]
    y_train = y_trainval[train_idx]

    X_val = X_trainval[val_idx]
    y_val = y_trainval[val_idx]

    print("[INFO] Train X:", X_train.shape)
    print("[INFO] Val X:", X_val.shape)
    print("[INFO] Test X:", X_test.shape)
    print("[INFO] Train groups:", len(set(groups_trainval[train_idx])))
    print("[INFO] Val groups:", len(set(groups_trainval[val_idx])))
    print("[INFO] Test groups:", len(set(groups_test)))

    # canal para Conv1D
    X_train = X_train[..., np.newaxis]
    X_val = X_val[..., np.newaxis]
    X_test = X_test[..., np.newaxis]

    classes = np.unique(y_train)
    class_weights_values = compute_class_weight(
        class_weight="balanced",
        classes=classes,
        y=y_train
    )
    class_weight = {int(c): float(w) for c, w in zip(classes, class_weights_values)}
    print("[INFO] Class weights:", class_weight)

    input_length = X_train.shape[1]
    num_classes = len(le.classes_)

    print("[STEP 2] Building model...")
    model = build_model(input_length=input_length, num_classes=num_classes)
    model.summary()

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=8,
            restore_best_weights=True
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=4,
            min_lr=1e-5
        ),
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(MODEL_FILE),
            monitor="val_loss",
            save_best_only=True
        ),
    ]

    print("[STEP 3] Training grouped CNN...")
    model.fit(
        X_train,
        y_train,
        validation_data=(X_val, y_val),
        epochs=40,
        batch_size=64,
        callbacks=callbacks,
        class_weight=class_weight,
        verbose=1,
    )

    print("[STEP 4] Evaluating on grouped test set...")
    y_prob = model.predict(X_test, verbose=0)
    y_pred = np.argmax(y_prob, axis=1)

    acc = accuracy_score(y_test, y_pred)
    print(f"\n=== ACCURACY ===\n{acc:.4f}")

    print("\n=== CLASSIFICATION REPORT ===")
    print(classification_report(y_test, y_pred, target_names=le.classes_, zero_division=0))

    print("\n=== CONFUSION MATRIX ===")
    print(confusion_matrix(y_test, y_pred))

    report_path = PROCESSED_DIR / "cnn_grouped_classification_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"Accuracy: {acc:.4f}\n\n")
        f.write(classification_report(y_test, y_pred, target_names=le.classes_, zero_division=0))
        f.write("\nConfusion Matrix:\n")
        f.write(str(confusion_matrix(y_test, y_pred)))

    print(f"\n[OK] Grouped model saved to: {MODEL_FILE}")
    print(f"[OK] Grouped report saved to: {report_path}")


if __name__ == "__main__":
    main()