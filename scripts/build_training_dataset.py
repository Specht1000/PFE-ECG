from src.config import ensure_directories
from scripts.run_batch_pipeline import run_batch
from src.dataset.merge_features import merge_feature_files
from src.dataset.auto_label import assign_simple_labels


def main():
    ensure_directories()

    print("[STEP 1] Running batch pipeline for all available records...")
    run_batch()

    print("\n[STEP 2] Merging all feature files...")
    merged_file = merge_feature_files()

    print("\n[STEP 3] Creating automatic labels...")
    assign_simple_labels(merged_file)

    print("\n[SUCCESS] Training dataset build completed successfully.")


if __name__ == "__main__":
    main()