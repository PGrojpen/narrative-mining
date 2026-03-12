from pathlib import Path
from tempfile import TemporaryDirectory

from src.preprocessing.metadata_extraction import load_selected_metadata

def main() -> None:
    test_ids = {222, 35661, 56371}

    with TemporaryDirectory() as tmpdir:
        books_folder = Path(tmpdir)

        for book_id in test_ids:
            (books_folder / f"{book_id}.txt").write_text("dummy", encoding="utf-8")

        metadata = load_selected_metadata()

        assert isinstance(metadata, dict), "metadata should be a dict"
        assert metadata, "metadata is empty"

        missing_ids = test_ids - set(metadata.keys())
        assert not missing_ids, f"missing metadata for IDs: {sorted(missing_ids)}"

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

    print("Metadata extraction smoke test passed.\n")

    for book_id in sorted(test_ids):
        book = metadata[book_id]
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