from pathlib import Path

# Root of the project
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_MITBIH_DIR = RAW_DIR / "mit_bih"

INTERIM_DIR = DATA_DIR / "interim"
CSV_DIR = INTERIM_DIR / "csv"
WINDOWS_DIR = INTERIM_DIR / "windows"

PROCESSED_DIR = DATA_DIR / "processed"

# Models
MODELS_DIR = PROJECT_ROOT / "models"
TRAINED_MODELS_DIR = MODELS_DIR / "trained"
EXPORTED_MODELS_DIR = MODELS_DIR / "exported"

# Reports
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"
LOGS_DIR = REPORTS_DIR / "logs"

# ECG settings
DEFAULT_RECORD = "100"
SAMPLING_RATE = 360
WINDOW_SIZE_SECONDS = 10
WINDOW_SIZE_SAMPLES = SAMPLING_RATE * WINDOW_SIZE_SECONDS

# Preferred ECG leads in order of priority
PREFERRED_SIGNAL_COLUMNS = ["MLII", "V5", "V1", "V2"]


def ensure_directories() -> None:
    dirs = [
        RAW_MITBIH_DIR,
        CSV_DIR,
        WINDOWS_DIR,
        PROCESSED_DIR,
        TRAINED_MODELS_DIR,
        EXPORTED_MODELS_DIR,
        FIGURES_DIR,
        TABLES_DIR,
        LOGS_DIR,
    ]

    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)