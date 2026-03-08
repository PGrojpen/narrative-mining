import csv
import random
import urllib.request

from pathlib import Path
from tqdm import tqdm
from src.config import TARGET_COUNT, SEED, LANGUAGE, BOOK_TYPE

CATALOG_URL = "https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv"
CATALOG_PATH = Path("data/gutenberg/metadata/pg_catalog.csv")

OUTPUT_PATH = Path(f"data/gutenberg/books_{TARGET_COUNT}_seed{SEED}.txt")

def ensure_dirs() -> None:
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

def download_catalog() -> None:
    if CATALOG_PATH.exists():
        print(f"Catalog already exists: {CATALOG_PATH}")
        return

    print(f"Downloading catalog from {CATALOG_URL} ...")
    urllib.request.urlretrieve(CATALOG_URL, CATALOG_PATH)
    print(f"Saved catalog to {CATALOG_PATH}")

def normalize(value: str | None) -> str:
    return (value or "").strip()

def parse_int(value: str | None) -> int | None:
    value = normalize(value)
    return int(value) if value.isdigit() else None

def looks_like_nonfiction(row: dict[str, str]) -> bool:
    text = " | ".join([
        normalize(row.get("Bookshelves")),
        normalize(row.get("Subjects")),
        normalize(row.get("Title")),
    ]).lower()

    blocked_terms = [
        "philosophy",
        "history",
        "biography",
        "autobiography",
        "memoir",
        "essays",
        "essay",
        "letters",
        "speeches",
        "sermons",
        "science",
        "mathematics",
        "politics",
        "government",
        "law",
        "religion",
        "theology",
        "criticism",
        "dictionary",
        "encyclopedia",
        "handbook",
        "manual",
        "guidebook",
        "treatise",
    ]

    return any(term in text for term in blocked_terms)

def row_matches(row: dict[str, str]) -> bool:
    language = normalize(row.get("Language")).lower()
    book_type = normalize(row.get("Type"))
    text_id = parse_int(row.get("Text#"))

    if text_id is None:
        return False

    if language != LANGUAGE:
        return False

    if book_type != BOOK_TYPE:
        return False

    if looks_like_nonfiction(row):
        return False

    return True

def load_matching_ids() -> list[int]:
    ids: list[int] = []

    with open(CATALOG_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        required_columns = {"Text#", "Language", "Type", "Title", "Subjects", "Bookshelves"}
        missing = required_columns - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"Missing expected columns in pg_catalog.csv: {sorted(missing)}\n"
                f"Found columns: {reader.fieldnames}"
            )

        for row in tqdm(reader, desc="Filtering catalog rows", unit="row"):
            if row_matches(row):
                text_id = parse_int(row.get("Text#"))
                if text_id is not None:
                    ids.append(text_id)

    return sorted(set(ids))

def save_ids(ids: list[int]) -> None:
    content = "\n".join(str(book_id) for book_id in ids) + "\n"
    OUTPUT_PATH.write_text(content, encoding="utf-8")

def main() -> None:
    ensure_dirs()
    download_catalog()

    ids = load_matching_ids()

    if len(ids) < TARGET_COUNT:
        raise ValueError(
            f"Only found {len(ids)} matching books, fewer than TARGET_COUNT={TARGET_COUNT}."
        )

    rng = random.Random(SEED)
    selected_ids = sorted(rng.sample(ids, TARGET_COUNT))

    save_ids(selected_ids)

    print(f"Saved {len(selected_ids)} IDs to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()