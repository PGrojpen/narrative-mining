from __future__ import annotations

import re

from pathlib import Path
from collections import Counter, defaultdict

from tqdm import tqdm


RAW_PATH = Path("data/gutenberg/raw")

CLOSING_ANCHORS = {
    "the_end_isolated": "the end",
    "end_isolated": "end",
    "finis_isolated": "finis",
    "fin_isolated": "fin",
}


def get_book_files(folder: Path) -> list[Path]:
    return sorted(
        path for path in folder.glob("*.txt")
        if path.is_file() and path.stem.isdigit()
    )


def read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def normalize_spaces(text: str) -> str:
    return " ".join(text.strip().split()).lower()


def strip_edge_ornaments(text: str) -> str:
    text = text.strip()

    text = re.sub(r"^[^\w]+", "", text)
    text = re.sub(r"[^\w]+$", "", text)

    text = re.sub(r"^[\W_]+", "", text)
    text = re.sub(r"[\W_]+$", "", text)

    return normalize_spaces(text)


def is_surrounded_by_blank_lines(lines: list[str], index: int) -> bool:
    if index == 0 or index == len(lines) - 1:
        return False

    prev_is_empty = not lines[index - 1].strip()
    next_is_empty = not lines[index + 1].strip()

    return prev_is_empty and next_is_empty


def detect_end_anchor_positions(text: str) -> dict[str, list[int]]:
    positions: dict[str, list[int]] = defaultdict(list)
    lines = text.splitlines()

    for index, line in enumerate(lines):
        if not is_surrounded_by_blank_lines(lines, index):
            continue

        cleaned = strip_edge_ornaments(line)
        if not cleaned:
            continue

        line_number = index + 1

        for anchor_name, anchor_value in CLOSING_ANCHORS.items():
            if cleaned == anchor_value:
                positions[anchor_name].append(line_number)

    return dict(positions)


def analyze_end_anchor_counts(folder: Path) -> tuple[dict[str, dict[str, int]], int]:
    book_files = get_book_files(folder)

    books_with_anchor: Counter[str] = Counter()
    books_with_exactly_one: Counter[str] = Counter()
    books_with_exactly_two: Counter[str] = Counter()
    books_with_three_or_more: Counter[str] = Counter()

    all_anchor_names = list(CLOSING_ANCHORS.keys())

    for file_path in tqdm(book_files, desc="Scanning endings", unit="book"):
        text = read_text_safe(file_path)
        anchor_positions = detect_end_anchor_positions(text)

        for anchor_name, positions in anchor_positions.items():
            count = len(positions)
            books_with_anchor[anchor_name] += 1

            if count == 1:
                books_with_exactly_one[anchor_name] += 1
            elif count == 2:
                books_with_exactly_two[anchor_name] += 1
            elif count >= 3:
                books_with_three_or_more[anchor_name] += 1

    summary: dict[str, dict[str, int]] = {}

    for anchor_name in all_anchor_names:
        summary[anchor_name] = {
            "books_with_anchor": books_with_anchor[anchor_name],
            "exactly_one": books_with_exactly_one[anchor_name],
            "exactly_two": books_with_exactly_two[anchor_name],
            "three_or_more": books_with_three_or_more[anchor_name],
        }

    return summary, len(book_files)


def main() -> None:
    summary, total_books = analyze_end_anchor_counts(RAW_PATH)

    print("END-ANCHOR REPORT")
    print("=" * 72)
    print(f"Books scanned: {total_books}")
    print()

    if total_books == 0:
        print("No .txt books found.")
        return

    for anchor_name, stats in sorted(
        summary.items(),
        key=lambda item: item[1]["books_with_anchor"],
        reverse=True,
    ):
        count = stats["books_with_anchor"]
        if count == 0:
            continue

        pct = (count / total_books) * 100

        print(anchor_name)
        print(f"  books_with_anchor: {count} ({pct:.2f}%)")
        print(f"  exactly_one:       {stats['exactly_one']}")
        print(f"  exactly_two:       {stats['exactly_two']}")
        print(f"  three_or_more:     {stats['three_or_more']}")
        print()


if __name__ == "__main__":
    main()