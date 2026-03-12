from __future__ import annotations

import re

from pathlib import Path
from collections import Counter, defaultdict

from tqdm import tqdm


RAW_PATH = Path("data/gutenberg/raw")


def build_anchor_pattern(left: str, right: str) -> re.Pattern[str]:
    return re.compile(
        rf"^\s*{left}\s+{right}(?:\s*[\.\:\-]\s*.*)?\s*$",
        re.IGNORECASE,
    )


FIRST_ANCHOR_PATTERNS: dict[str, re.Pattern[str]] = {
    "chapter_i": build_anchor_pattern(r"chapter", r"i"),
    "chapter_1": build_anchor_pattern(r"chapter", r"1"),
    "chapter_one": build_anchor_pattern(r"chapter", r"one"),
    "chapter_first": build_anchor_pattern(r"chapter", r"first"),
    "chapter_the_first": build_anchor_pattern(r"chapter", r"the\s+first"),
    "first_chapter": build_anchor_pattern(r"first", r"chapter"),

    "chap_i": build_anchor_pattern(r"chap\.?", r"i"),
    "chap_1": build_anchor_pattern(r"chap\.?", r"1"),
    "chap_one": build_anchor_pattern(r"chap\.?", r"one"),
    "chap_first": build_anchor_pattern(r"chap\.?", r"first"),

    "book_i": build_anchor_pattern(r"book", r"i"),
    "book_1": build_anchor_pattern(r"book", r"1"),
    "book_one": build_anchor_pattern(r"book", r"one"),
    "book_first": build_anchor_pattern(r"book", r"first"),
    "book_the_first": build_anchor_pattern(r"book", r"the\s+first"),
    "first_book": build_anchor_pattern(r"first", r"book"),

    "part_i": build_anchor_pattern(r"part", r"i"),
    "part_1": build_anchor_pattern(r"part", r"1"),
    "part_one": build_anchor_pattern(r"part", r"one"),
    "part_first": build_anchor_pattern(r"part", r"first"),
    "part_the_first": build_anchor_pattern(r"part", r"the\s+first"),
    "first_part": build_anchor_pattern(r"first", r"part"),

    "letter_i": build_anchor_pattern(r"letter", r"i"),
    "letter_1": build_anchor_pattern(r"letter", r"1"),
    "letter_one": build_anchor_pattern(r"letter", r"one"),
    "letter_first": build_anchor_pattern(r"letter", r"first"),
    "letter_the_first": build_anchor_pattern(r"letter", r"the\s+first"),
    "first_letter": build_anchor_pattern(r"first", r"letter"),
}


def get_book_files(folder: Path) -> list[Path]:
    return sorted(
        path for path in folder.glob("*.txt")
        if path.is_file() and path.stem.isdigit()
    )


def is_isolated_roman_i(lines: list[str], index: int) -> bool:
    current = lines[index].strip()
    if current != "I":
        return False

    if index == 0 or index == len(lines) - 1:
        return False

    prev_is_empty = not lines[index - 1].strip()
    next_is_empty = not lines[index + 1].strip()

    return prev_is_empty and next_is_empty


def detect_first_anchor_positions(text: str) -> dict[str, list[int]]:
    positions: dict[str, list[int]] = defaultdict(list)
    lines = text.splitlines()

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        line_number = index + 1

        for anchor_name, pattern in FIRST_ANCHOR_PATTERNS.items():
            if pattern.match(stripped):
                positions[anchor_name].append(line_number)

        if is_isolated_roman_i(lines, index):
            positions["roman_i_isolated"].append(line_number)

    return dict(positions)


def analyze_first_anchor_counts(folder: Path) -> tuple[dict[str, dict[str, int]], int]:
    book_files = get_book_files(folder)

    books_with_anchor: Counter[str] = Counter()
    books_with_exactly_one: Counter[str] = Counter()
    books_with_exactly_two: Counter[str] = Counter()
    books_with_three_or_more: Counter[str] = Counter()

    all_anchor_names = list(FIRST_ANCHOR_PATTERNS.keys()) + ["roman_i_isolated"]

    for file_path in tqdm(book_files, desc="Scanning books", unit="book"):
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = file_path.read_text(encoding="utf-8", errors="ignore")

        anchor_positions = detect_first_anchor_positions(text)

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
    summary, total_books = analyze_first_anchor_counts(RAW_PATH)

    print("FIRST-ANCHOR REPORT")
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