from pathlib import Path

TARGET_COUNT = 1200
TARGET_VALID_BOOKS = 1000
SEED = 42
LANGUAGE = "en"
BOOK_TYPE = "Text"

BASE_DIR = Path(__file__).resolve().parent
RAW_PATH = BASE_DIR / "data" / "gutenberg" / "raw"
PRE_CLEANED_PATH = BASE_DIR / "data" / "gutenberg" / "processed" / "pre_cleaned"
INSPECTION_PATH = BASE_DIR / "data" / "gutenberg" / "inspection"