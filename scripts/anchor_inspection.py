import re

from pathlib import Path
from collections import Counter, defaultdict

from tqdm import tqdm


RAW_PATH = Path("data/gutenberg/raw")


# =========================
# Helpers
# =========================

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


# =========================
# Closing anchors
# =========================

CLOSING_ANCHORS = {
    "the_end_isolated": "the end",
    "end_isolated": "end",
    "finis_isolated": "finis",
    "fin_isolated": "fin",
}


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


# =========================
# Opening anchors
# =========================

def build_anchor_pattern(left: str, right: str) -> re.Pattern[str]:
    return re.compile(
        rf"^\s*{left}\s+{right}(?:\s*[\.\:\-]\s*.*)?\s*$",
        re.IGNORECASE,
    )


START_ANCHOR_PATTERNS: dict[str, re.Pattern[str]] = {
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


def is_isolated_roman_i(lines: list[str], index: int) -> bool:
    current = lines[index].strip()
    if current != "I":
        return False

    if index == 0 or index == len(lines) - 1:
        return False

    prev_is_empty = not lines[index - 1].strip()
    next_is_empty = not lines[index + 1].strip()

    return prev_is_empty and next_is_empty


def detect_start_anchor_positions(text: str) -> dict[str, list[int]]:
    positions: dict[str, list[int]] = defaultdict(list)
    lines = text.splitlines()

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        line_number = index + 1

        for anchor_name, pattern in START_ANCHOR_PATTERNS.items():
            if pattern.match(stripped):
                positions[anchor_name].append(line_number)

        if is_isolated_roman_i(lines, index):
            positions["roman_i_isolated"].append(line_number)

    return dict(positions)

def update_anchor_counters(
    anchor_positions: dict[str, list[int]],
    books_with_anchor: Counter[str],
    books_with_exactly_one: Counter[str],
    books_with_exactly_two: Counter[str],
    books_with_three_or_more: Counter[str],
) -> None:
    for anchor_name, positions in anchor_positions.items():
        count = len(positions)
        books_with_anchor[anchor_name] += 1

        if count == 1:
            books_with_exactly_one[anchor_name] += 1
        elif count == 2:
            books_with_exactly_two[anchor_name] += 1
        elif count >= 3:
            books_with_three_or_more[anchor_name] += 1


def build_summary(
    all_anchor_names: list[str],
    books_with_anchor: Counter[str],
    books_with_exactly_one: Counter[str],
    books_with_exactly_two: Counter[str],
    books_with_three_or_more: Counter[str],
) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {}

    for anchor_name in all_anchor_names:
        summary[anchor_name] = {
            "books_with_anchor": books_with_anchor[anchor_name],
            "exactly_one": books_with_exactly_one[anchor_name],
            "exactly_two": books_with_exactly_two[anchor_name],
            "three_or_more": books_with_three_or_more[anchor_name],
        }

    return summary


def analyze_anchor_counts(
    folder: Path,
) -> tuple[dict[str, dict[str, int]], dict[str, dict[str, int]], int]:
    book_files = get_book_files(folder)

    start_books_with_anchor: Counter[str] = Counter()
    start_books_with_exactly_one: Counter[str] = Counter()
    start_books_with_exactly_two: Counter[str] = Counter()
    start_books_with_three_or_more: Counter[str] = Counter()

    end_books_with_anchor: Counter[str] = Counter()
    end_books_with_exactly_one: Counter[str] = Counter()
    end_books_with_exactly_two: Counter[str] = Counter()
    end_books_with_three_or_more: Counter[str] = Counter()

    all_start_anchor_names = list(START_ANCHOR_PATTERNS.keys()) + ["roman_i_isolated"]
    all_end_anchor_names = list(CLOSING_ANCHORS.keys())

    for file_path in tqdm(book_files, desc="Scanning anchors", unit="book"):
        text = read_text_safe(file_path)

        start_anchor_positions = detect_start_anchor_positions(text)
        end_anchor_positions = detect_end_anchor_positions(text)

        update_anchor_counters(
            start_anchor_positions,
            start_books_with_anchor,
            start_books_with_exactly_one,
            start_books_with_exactly_two,
            start_books_with_three_or_more,
        )

        update_anchor_counters(
            end_anchor_positions,
            end_books_with_anchor,
            end_books_with_exactly_one,
            end_books_with_exactly_two,
            end_books_with_three_or_more,
        )

    start_summary = build_summary(
        all_start_anchor_names,
        start_books_with_anchor,
        start_books_with_exactly_one,
        start_books_with_exactly_two,
        start_books_with_three_or_more,
    )

    end_summary = build_summary(
        all_end_anchor_names,
        end_books_with_anchor,
        end_books_with_exactly_one,
        end_books_with_exactly_two,
        end_books_with_three_or_more,
    )

    return start_summary, end_summary, len(book_files)


def print_summary(
    title: str,
    summary: dict[str, dict[str, int]],
    total_books: int,
) -> None:
    print(title)
    print("=" * 72)
    print(f"Books scanned: {total_books}")
    print()

    if total_books == 0:
        print("No .txt books found.")
        print()
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


def main() -> None:
    start_summary, end_summary, total_books = analyze_anchor_counts(RAW_PATH)

    print_summary("START-ANCHOR REPORT", start_summary, total_books)
    print_summary("END-ANCHOR REPORT", end_summary, total_books)


if __name__ == "__main__":
    main()