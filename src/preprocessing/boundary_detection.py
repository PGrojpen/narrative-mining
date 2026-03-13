import re
from pathlib import Path
from typing import Optional

OPENING_PATTERN = re.compile(
    r"^\s*chapter\s+i(?:\s*[\.\:\-]\s*.*)?\s*$",
    re.IGNORECASE,
)

# aceita chapter II, chapter 2, chapter xvi, etc.
CHAPTER_HEADING_PATTERN = re.compile(
    r"^\s*chapter\s+(?:[ivxlcdm]+|\d+)(?:\s*[\.\:\-]\s*.*)?\s*$",
    re.IGNORECASE,
)


def normalize_opening_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip().lower())


def normalize_closing_line(line: str) -> str:
    cleaned = re.sub(r"[_=*~\-–—#.`'\":;,\[\]\(\)\{\}|\\/<>]+", " ", line)
    return re.sub(r"\s+", " ", cleaned).strip().lower()


def is_blank_line(line: str) -> bool:
    return line.strip() == ""


def looks_like_chapter_heading(line: str) -> bool:
    return CHAPTER_HEADING_PATTERN.match(line.strip()) is not None


def is_probable_toc(lines: list[str], opening_idx: int, window: int = 20, min_hits: int = 3) -> bool:
    hits = 0
    checked = 0

    for i in range(opening_idx + 1, len(lines)):
        line = lines[i].strip()

        if not line:
            continue

        checked += 1

        if looks_like_chapter_heading(line):
            hits += 1

        if checked >= window:
            break

    return hits >= min_hits


def find_opening_anchor(lines: list[str]) -> tuple[Optional[int], str]:
    valid_matches: list[int] = []
    toc_like_matches: list[int] = []

    for i, line in enumerate(lines):
        if not OPENING_PATTERN.match(line.strip()):
            continue

        if is_probable_toc(lines, i):
            toc_like_matches.append(i)
            continue

        valid_matches.append(i)

    if len(valid_matches) == 1:
        return valid_matches[0], "ok"

    if len(valid_matches) == 0:
        if len(toc_like_matches) > 0:
            return None, "opening_is_toc"
        return None, "no_valid_opening"

    return None, "too_many_openings"


def find_closing_anchor(lines: list[str], start_idx: int) -> tuple[Optional[int], str]:
    matches: list[int] = []

    for i in range(start_idx, len(lines)):
        if normalize_closing_line(lines[i]) != "the end":
            continue

        if i == 0 or i == len(lines) - 1:
            continue

        if is_blank_line(lines[i - 1]) and is_blank_line(lines[i + 1]):
            matches.append(i)

    if len(matches) == 0:
        return None, "no_valid_closing"
    if len(matches) == 1:
        return matches[0], "ok"
    return None, "multiple_valid_closings"


def bound_text(text: str) -> tuple[Optional[str], str]:
    lines = text.splitlines()

    start_idx, opening_status = find_opening_anchor(lines)
    if start_idx is None:
        return None, opening_status

    end_idx, closing_status = find_closing_anchor(lines, start_idx + 1)
    if end_idx is None:
        return None, closing_status

    if end_idx <= start_idx:
        return None, "closing_before_opening"

    bounded_lines = lines[start_idx:end_idx + 1]
    bounded_text = "\n".join(bounded_lines).strip() + "\n"
    return bounded_text, "saved"


def process_file(input_path: Path, output_path: Path) -> str:
    try:
        text = input_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = input_path.read_text(encoding="utf-8", errors="ignore")

    bounded, status = bound_text(text)

    if bounded is None:
        return status

    output_path.write_text(bounded, encoding="utf-8")
    return status