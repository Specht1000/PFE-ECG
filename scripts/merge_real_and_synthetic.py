import pandas as pd

real_path = "data/processed/rr_train_grouped.csv"
synthetic_path = "data/processed/synthetic_features.csv"

output_path = "data/processed/rr_train_augmented.csv"

real = pd.read_csv(real_path)
synthetic = pd.read_csv(synthetic_path)

# garantir mesmas colunas
common_cols = list(set(real.columns) & set(synthetic.columns))

real = real[common_cols]
synthetic = synthetic[common_cols]

df = pd.concat([real, synthetic], ignore_index=True)

df.to_csv(output_path, index=False)

print("Saved merged dataset:", output_path)
print(df["label"].value_counts())