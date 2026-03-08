import csv

from pathlib import Path


CATALOG_PATH = Path("data/gutenberg/metadata/pg_catalog.csv")


def normalize(value: str | None) -> str:
    return (value or "").strip()


def split_multivalue(value: str | None, sep: str = ";") -> list[str]:
    value = normalize(value)
    if not value:
        return []
    return [part.strip() for part in value.split(sep) if part.strip()]


def parse_book_metadata(row: dict[str, str]) -> dict:
    return {
        "book_id": int(normalize(row["Text#"])),
        "title": normalize(row.get("Title")),
        "authors": split_multivalue(row.get("Authors")),
        "language": normalize(row.get("Language")).lower(),
        "type": normalize(row.get("Type")),
        "issued": normalize(row.get("Issued")),
        "subjects": split_multivalue(row.get("Subjects")),
        "bookshelves": split_multivalue(row.get("Bookshelves")),
        "locc": split_multivalue(row.get("LoCC")),
    }


def load_selected_metadata(selected_ids: set[int], catalog_path: Path = CATALOG_PATH,) -> dict[int, dict]:
    
    metadata_by_id: dict[int, dict] = {}

    with open(catalog_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        required_columns = {
            "Text#",
            "Title",
            "Authors",
            "Language",
            "Type",
            "Issued",
            "Subjects",
            "Bookshelves",
            "LoCC",
        }
        missing = required_columns - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"Missing expected columns in pg_catalog.csv: {sorted(missing)}\n"
                f"Found columns: {reader.fieldnames}"
            )

        for row in reader:
            text_id = normalize(row.get("Text#"))
            if not text_id.isdigit():
                continue

            book_id = int(text_id)
            if book_id not in selected_ids:
                continue

            metadata_by_id[book_id] = parse_book_metadata(row)

    return metadata_by_id