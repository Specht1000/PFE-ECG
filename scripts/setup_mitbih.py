from pathlib import Path
import shutil
import zipfile

from src.config import RAW_MITBIH_DIR, ensure_directories

VALID_EXTENSIONS = {".dat", ".hea", ".atr"}
VALID_FILENAMES = {"RECORDS", "ANNOTATORS"}


def extract_mitbih_zip(zip_path: Path) -> None:
    """
    Extract MIT-BIH ZIP and copy useful files to data/raw/mit_bih.
    """

    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP file not found: {zip_path}")

    ensure_directories()

    temp_extract_dir = RAW_MITBIH_DIR.parent / "_tmp_extract"

    if temp_extract_dir.exists():
        shutil.rmtree(temp_extract_dir)

    temp_extract_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Extracting ZIP file: {zip_path}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(temp_extract_dir)

    copied = 0

    for file_path in temp_extract_dir.rglob("*"):
        if file_path.is_file():
            if (
                file_path.suffix.lower() in VALID_EXTENSIONS
                or file_path.name in VALID_FILENAMES
            ):
                destination = RAW_MITBIH_DIR / file_path.name
                shutil.copy2(file_path, destination)
                copied += 1

    shutil.rmtree(temp_extract_dir)

    print("[INFO] Extraction completed successfully.")
    print(f"[INFO] Files copied to: {RAW_MITBIH_DIR}")
    print(f"[INFO] Total useful files copied: {copied}")


if __name__ == "__main__":
    # Put the ZIP file in the project root, or adjust this path if needed
    zip_file = Path("mit-bih-arrhythmia-database-1.0.0.zip")
    extract_mitbih_zip(zip_file)