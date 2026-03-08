from pathlib import Path
from urllib.request import urlretrieve
from urllib.error import URLError, HTTPError
from tqdm import tqdm

from src.config import TARGET_VALID_BOOKS, TARGET_COUNT, SEED

RAW_DIR = Path("data/gutenberg/raw")
BOOK_IDS_PATH = Path(f"data/gutenberg/books_{TARGET_COUNT}_seed{SEED}.txt")

RAW_DIR.mkdir(parents=True, exist_ok=True)

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


def main() -> None:
    book_ids = load_book_ids()
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
            )

            if valid_books >= TARGET_VALID_BOOKS:
                break

    checked = downloaded + skipped + failed

    print("\nDownload summary")
    print(f"Downloaded: {downloaded}")
    print(f"Skipped:    {skipped}")
    print(f"Failed:     {failed}")
    print(f"Total:      {checked}")


if __name__ == "__main__":
    main()