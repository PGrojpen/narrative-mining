import csv
import random
import urllib.request

from pathlib import Path
from urllib.request import urlretrieve
from urllib.error import URLError, HTTPError

from tqdm import tqdm

from src.config import TARGET_VALID_BOOKS, TARGET_COUNT, SEED, LANGUAGE, BOOK_TYPE

CATALOG_URL = "https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv"
CATALOG_PATH = Path("data/gutenberg/metadata/pg_catalog.csv")

BOOK_IDS_PATH = Path(f"data/gutenberg/books_{TARGET_COUNT}_seed{SEED}.txt")
RAW_DIR = Path("data/gutenberg/raw")

def ensure_dirs() -> None:
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    BOOK_IDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

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
    BOOK_IDS_PATH.write_text(content, encoding="utf-8")

def build_book_list() -> list[int]:
    print("\n[1/2] Building book list...")
    download_catalog()

    ids = load_matching_ids()

    if len(ids) < TARGET_COUNT:
        raise ValueError(
            f"Only found {len(ids)} matching books, fewer than TARGET_COUNT={TARGET_COUNT}."
        )

    rng = random.Random(SEED)
    selected_ids = sorted(rng.sample(ids, TARGET_COUNT))

    save_ids(selected_ids)

    print(f"Saved {len(selected_ids)} IDs to {BOOK_IDS_PATH}")
    return selected_ids

def load_book_ids(path: Path = BOOK_IDS_PATH) -> list[int]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [int(line.strip()) for line in lines if line.strip()]

def get_candidate_urls(book_id: int) -> list[str]:
    return [
        f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt",
    ]

def is_too_small(path: Path, min_chars: int = 50000) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return True

    return len(text) < min_chars

def is_html_file(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
    except Exception:
        return True

    return "<html" in text or "<!doctype html" in text

def is_valid_text_file(path: Path, min_chars: int = 50000) -> bool:
    if is_too_small(path, min_chars=min_chars):
        return False

    if is_html_file(path):
        return False

    return True

def download_book(book_id: int) -> str:
    output_path = RAW_DIR / f"{book_id}.txt"

    if output_path.exists() and is_valid_text_file(output_path):
        return "skipped"

    if output_path.exists():
        output_path.unlink(missing_ok=True)

    for url in get_candidate_urls(book_id):
        try:
            urlretrieve(url, output_path)

            if is_valid_text_file(output_path):
                return "downloaded"

            output_path.unlink(missing_ok=True)

        except (HTTPError, URLError, TimeoutError, OSError):
            continue

    output_path.unlink(missing_ok=True)
    return "failed"

def download_books(book_ids: list[int]) -> None:
    print("\n[2/2] Downloading books...")

    valid_books = 0
    downloaded = 0
    skipped = 0
    failed = 0

    with tqdm(book_ids, desc="Downloading books", unit="book") as pbar:
        for book_id in pbar:
            result = download_book(book_id)

            if result == "downloaded":
                downloaded += 1
                valid_books += 1
            elif result == "skipped":
                skipped += 1
                valid_books += 1
            else:
                failed += 1
                tqdm.write(f"Failed: {book_id}")

            pbar.set_postfix(
                downloaded=downloaded,
                skipped=skipped,
                failed=failed,
                valid=valid_books,
            )

            if valid_books >= TARGET_VALID_BOOKS:
                break

    checked = downloaded + skipped + failed

    print("\nDownload summary")
    print(f"Downloaded: {downloaded}")
    print(f"Skipped:    {skipped}")
    print(f"Failed:     {failed}")
    print(f"Checked:    {checked}")
    print(f"Valid books:{valid_books}")

def main() -> None:
    ensure_dirs()

    try:
        book_ids = build_book_list()
    except Exception as e:
        print(f"\nBook list build failed: {e}")
        return

    download_books(book_ids)

if __name__ == "__main__":
    main()