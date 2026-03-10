from pathlib import Path
import requests


def build_candidate_urls(book_id: int) -> list[str]:
    book_id_str = str(book_id)

    return [
        f"https://www.gutenberg.org/ebooks/{book_id}.txt.utf-8",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}-8.txt",
    ]


def download_gutenberg_book(book_id: int, output_dir: str = "data/gutenberg/raw") -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; NarrativeMiningBot/1.0)"
    }

    last_error = None

    for url in build_candidate_urls(book_id):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200 and response.text.strip():
                file_path = output_path / f"{book_id}.txt"
                file_path.write_text(response.text, encoding="utf-8")
                print(f"Downloaded book {book_id} from: {url}")
                print(f"Saved to: {file_path}")
                return file_path
        except requests.RequestException as e:
            last_error = e

    raise RuntimeError(
        f"Could not download book {book_id}. Last error: {last_error}"
    )


if __name__ == "__main__":
    BOOK_ID = 53769
    download_gutenberg_book(BOOK_ID)