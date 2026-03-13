import random

from src.preprocessing.metadata_extraction import load_selected_metadata
from config import SEED, TESTS_PATH

SAMPLE_SIZE = 3


def main() -> None:
    TESTS_PATH.mkdir(parents=True, exist_ok=True)

    output_dir = TESTS_PATH / "metadata"
    output_dir.mkdir(parents=True, exist_ok=True)

    random.seed(SEED)

    metadata = load_selected_metadata()

    assert isinstance(metadata, dict), "metadata should be a dict"
    assert metadata, "metadata is empty"

    available_ids = sorted(metadata.keys())
    sample_size = min(SAMPLE_SIZE, len(available_ids))
    test_ids = random.sample(available_ids, k=sample_size)

    print("Metadata extraction smoke test passed.\n")

    for book_id in sorted(test_ids):
        book = metadata[book_id]

        assert isinstance(book, dict), f"book {book_id} metadata should be a dict"
        assert book["book_id"] == book_id, f"book_id mismatch for {book_id}"
        assert isinstance(book["title"], str), f"title should be str for {book_id}"
        assert isinstance(book["authors"], list), f"authors should be list for {book_id}"
        assert isinstance(book["language"], str), f"language should be str for {book_id}"
        assert isinstance(book["type"], str), f"type should be str for {book_id}"
        assert isinstance(book["issued"], str), f"issued should be str for {book_id}"
        assert isinstance(book["subjects"], list), f"subjects should be list for {book_id}"
        assert isinstance(book["bookshelves"], list), f"bookshelves should be list for {book_id}"
        assert isinstance(book["locc"], list), f"locc should be list for {book_id}"

        result = (
            f"BOOK ID: {book_id}\n"
            f"Title: {book['title']}\n"
            f"Authors: {book['authors']}\n"
            f"Language: {book['language']}\n"
            f"Type: {book['type']}\n"
            f"Issued: {book['issued']}\n"
            f"Subjects sample: {book['subjects'][:3]}\n"
            f"Bookshelves sample: {book['bookshelves'][:3]}\n"
            f"LoCC: {book['locc']}\n"
            + "-" * 60
        )

        (output_dir / f"{book_id}.txt").write_text(result, encoding="utf-8")

        print(f"BOOK ID: {book_id}")
        print(f"Title: {book['title']}")
        print(f"Authors: {book['authors']}")
        print(f"Language: {book['language']}")
        print(f"Type: {book['type']}")
        print(f"Issued: {book['issued']}")
        print(f"Subjects sample: {book['subjects'][:3]}")
        print(f"Bookshelves sample: {book['bookshelves'][:3]}")
        print(f"LoCC: {book['locc']}")
        print("-" * 60)


if __name__ == "__main__":
    main()