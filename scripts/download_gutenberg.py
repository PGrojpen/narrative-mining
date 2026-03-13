import csv
import re
import urllib.request

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import URLError, HTTPError

from tqdm import tqdm

from config import RAW_PATH, CATALOG_PATH, LANGUAGE, BOOK_TYPE


CATALOG_URL = "https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv"
BOOK_IDS_PATH = Path("data/gutenberg/books_all_narrative_candidates.txt")

MAX_WORKERS = 12
MIN_WORD_COUNT = 40000
TIMEOUT_SECONDS = 20
USER_AGENT = "NarrativeMining/1.0"


def ensure_dirs() -> None:
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    BOOK_IDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_PATH.mkdir(parents=True, exist_ok=True)


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


def joined_metadata_text(row: dict[str, str]) -> str:
    return " | ".join([
        normalize(row.get("Bookshelves")),
        normalize(row.get("Subjects")),
        normalize(row.get("Title")),
    ]).lower()


def split_locc_codes(raw_locc: str) -> list[str]:
    if not raw_locc:
        return []

    normalized = raw_locc.replace(",", ";")
    return [code.strip().upper() for code in normalized.split(";") if code.strip()]


def has_allowed_locc(row: dict[str, str]) -> bool:
    locc = normalize(row.get("LoCC"))
    codes = split_locc_codes(locc)

    allowed_prefixes = ("PR", "PS", "PZ", "PQ", "PT", "PG")

    return any(code.startswith(allowed_prefixes) for code in codes)


def looks_like_nonfiction(row: dict[str, str]) -> bool:
    text = joined_metadata_text(row)

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
        "catalog",
        "catalogue",
        "index",
        "bibliography",
        "lectures",
        "report",
        "reports",
        "proceedings",
        "paper",
        "papers",
        "address",
        "addresses",
        "tract",
        "tracts",
        "reference",
        "study",
        "studies",
    ]

    return any(term in text for term in blocked_terms)


def looks_like_poetry_or_drama(row: dict[str, str]) -> bool:
    text = joined_metadata_text(row)

    blocked_terms = [
        "poetry",
        "poems",
        "poem",
        "verse",
        "ballads",
        "hymns",
        "drama",
        "play",
        "plays",
        "tragedy",
        "comedies",
        "comedy",
        "theater",
        "theatre",
    ]

    return any(term in text for term in blocked_terms)


def looks_like_fiction(row: dict[str, str]) -> bool:
    text = joined_metadata_text(row)

    fiction_terms = [
        "fiction",
        "novel",
        "novels",
        "short stories",
        "story",
        "stories",
        "science fiction",
        "fantasy",
        "detective",
        "mystery",
        "adventure",
        "romance",
        "horror",
        "ghost stories",
        "juvenile fiction",
        "children's literature",
        "historical fiction",
        "war stories",
        "western stories",
        "sea stories",
    ]

    return any(term in text for term in fiction_terms)


def get_matching_text_id(row: dict[str, str]) -> int | None:
    language = normalize(row.get("Language")).lower()
    book_type = normalize(row.get("Type"))
    text_id = parse_int(row.get("Text#"))

    if text_id is None:
        return None

    if language != LANGUAGE:
        return None

    if book_type != BOOK_TYPE:
        return None

    if looks_like_nonfiction(row):
        return None

    if looks_like_poetry_or_drama(row):
        return None

    if not (looks_like_fiction(row) and has_allowed_locc(row)):
        return None

    return text_id


def load_matching_ids() -> list[int]:
    ids: list[int] = []

    with open(CATALOG_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        for row in tqdm(reader, desc="Filtering catalog rows", unit="row"):
            text_id = get_matching_text_id(row)
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

    if not ids:
        raise ValueError("No matching books found.")

    save_ids(ids)

    print(f"Saved {len(ids)} IDs to {BOOK_IDS_PATH}")
    return ids


def load_book_ids(path: Path = BOOK_IDS_PATH) -> list[int]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [int(line.strip()) for line in lines if line.strip()]


def get_candidate_urls(book_id: int) -> list[str]:
    return [
        f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt",
    ]


def read_text_safe(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w']+\b", text))

def validate_text_file(path: Path) -> bool:
    text = read_text_safe(path)
    if text is None:
        return False

    lowered = text.lower()

    word_count = count_words(text)
    if word_count < MIN_WORD_COUNT:
        return False

    if "<html" in lowered or "<!doctype html" in lowered:
        return False

    return True


def download_to_path(url: str, output_path: Path) -> None:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT},
    )

    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
        data = response.read()

    output_path.write_bytes(data)


def download_book(book_id: int) -> str:
    output_path = RAW_PATH / f"{book_id}.txt"

    if output_path.exists():
        if validate_text_file(output_path):
            return "skipped"
        output_path.unlink(missing_ok=True)

    for url in get_candidate_urls(book_id):
        try:
            download_to_path(url, output_path)

            if not validate_text_file(output_path):
                output_path.unlink(missing_ok=True)
                continue

            return "downloaded"

        except (HTTPError, URLError, TimeoutError, OSError):
            output_path.unlink(missing_ok=True)
            continue

    output_path.unlink(missing_ok=True)
    return "failed"


def download_books(book_ids: list[int]) -> None:
    print("\n[2/2] Downloading books...")

    downloaded = 0
    skipped = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(download_book, book_id) for book_id in book_ids]

        with tqdm(total=len(book_ids), desc="Downloading books", unit="book") as pbar:
            for future in as_completed(futures):
                result = future.result()

                if result == "downloaded":
                    downloaded += 1
                elif result == "skipped":
                    skipped += 1
                else:
                    failed += 1

                pbar.update(1)
                pbar.set_postfix(
                    downloaded=downloaded,
                    skipped=skipped,
                    failed=failed,
                    valid=downloaded + skipped,
                )

    checked = downloaded + skipped + failed
    valid_books = downloaded + skipped

    print("\nDownload summary")
    print(f"Downloaded:  {downloaded}")
    print(f"Skipped:     {skipped}")
    print(f"Failed:      {failed}")
    print(f"Checked:     {checked}")
    print(f"Valid books: {valid_books}")


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