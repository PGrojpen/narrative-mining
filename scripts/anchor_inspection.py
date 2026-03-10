from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from config import PRE_CLEANED_PATH, INSPECTION_PATH, TARGET_COUNT, SEED

MAX_FILES = 1000
MAX_LINES_PER_FILE = 200
TOP_N = 100

ROMAN_PATTERN = re.compile(r"\b[IVXLCDM]+\b")
YEAR_PATTERN = re.compile(r"\b(1[6-9]\d{2}|20\d{2})\b")
NUMBER_PATTERN = re.compile(r"\b\d+\b")
WHITESPACE_PATTERN = re.compile(r"\s+")

LABELLED_LINE_PATTERN = re.compile(
    r"^(title|author|language|release date|illustrations|contents|index|chapter|page)\b[:.]?",
    re.IGNORECASE,
)


def read_first_lines(file_path: Path, max_lines: int = MAX_LINES_PER_FILE) -> list[str]:
    with file_path.open("r", encoding="utf-8") as f:
        return [line.rstrip("\n") for _, line in zip(range(max_lines), f)]


def normalize_line(line: str) -> str:
    line = line.strip()

    if not line:
        return "<EMPTY>"

    normalized = line.upper()

    normalized = YEAR_PATTERN.sub("<YEAR>", normalized)
    normalized = ROMAN_PATTERN.sub("<ROMAN>", normalized)
    normalized = NUMBER_PATTERN.sub("<NUM>", normalized)

    normalized = WHITESPACE_PATTERN.sub(" ", normalized).strip()

    if re.fullmatch(r"[\*\-_=~ ]{3,}", normalized):
        return "<SEPARATOR>"

    if normalized.startswith("[ILLUSTRATION:"):
        return "[ILLUSTRATION: ...]"

    if LABELLED_LINE_PATTERN.match(normalized):
        return normalized

    if normalized.startswith("BY "):
        return "BY <TEXT>"

    if normalized.startswith("CHAPTER "):
        return "CHAPTER <TEXT>"

    if normalized.startswith("BOOK "):
        return "BOOK <TEXT>"

    if normalized.startswith("PART "):
        return "PART <TEXT>"

    return normalized


def iter_text_files(folder: Path, max_files: int = MAX_FILES) -> list[Path]:
    files = sorted(folder.glob("*.txt"))
    return files[:max_files]


def build_report(raw_counter: Counter[str], normalized_counter: Counter[str]) -> str:
    lines: list[str] = []

    lines.append("COMMON FRONT-MATTER PATTERNS REPORT")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Top raw lines: {TOP_N}")
    lines.append(f"Top normalized patterns: {TOP_N}")
    lines.append("")

    lines.append("TOP RAW LINES")
    lines.append("-" * 60)
    for line, count in raw_counter.most_common(TOP_N):
        lines.append(f"{count:>4} | {repr(line)}")

    lines.append("")
    lines.append("TOP NORMALIZED PATTERNS")
    lines.append("-" * 60)
    for line, count in normalized_counter.most_common(TOP_N):
        lines.append(f"{count:>4} | {repr(line)}")

    return "\n".join(lines)


def main() -> None:
    output_file = INSPECTION_PATH / f"common_front_patterns_{TARGET_COUNT}_seed{SEED}.txt"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    raw_counter: Counter[str] = Counter()
    normalized_counter: Counter[str] = Counter()

    files = iter_text_files(PRE_CLEANED_PATH, max_files=MAX_FILES)

    for file_path in files:
        lines = read_first_lines(file_path, MAX_LINES_PER_FILE)

        for line in lines:
            stripped = line.strip()
            raw_counter[stripped] += 1
            normalized_counter[normalize_line(stripped)] += 1

    report = build_report(raw_counter, normalized_counter)
    output_file.write_text(report, encoding="utf-8")

    print(f"Analyzed {len(files)} files.")
    print(f"Report saved to: {output_file}")


if __name__ == "__main__":
    main()