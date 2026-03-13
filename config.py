from pathlib import Path

TARGET_COUNT = 1200
TARGET_VALID_BOOKS = 1000
SEED = 42
LANGUAGE = "en"
BOOK_TYPE = "Text"

BASE_DIR = Path(__file__).resolve().parent
CATALOG_PATH = BASE_DIR/ "data" /"gutenberg"/"metadata"/"pg_catalog.csv"
RAW_PATH = BASE_DIR/"data"/"gutenberg"/"raw"
INSPECTION_PATH = BASE_DIR/"data"/"gutenberg"/"inspection"
BOUNDED_PATH = BASE_DIR/"data"/"gutenberg"/"processed"/"bounded"