import re
from pathlib import Path
from typing import Optional


TOC_WINDOW_NONEMPTY_LINES = 40
TOC_MIN_CHAPTER_ENTRY_COUNT = 3

OPENING_MIN_RELATIVE_POSITION = 0.0
OPENING_MAX_RELATIVE_POSITION = 0.05
CLOSING_MIN_RELATIVE_POSITION = 0.90


CHAPTER_I_OPENING_RE = re.compile(
    r"^\s*chapter\s+i\b(?:\s*[\.\:\-–—_]*\s*.*)?\s*$",
    re.IGNORECASE,
)

CHAPTER_ENTRY_RE = re.compile(
    r"^\s*chapter\s+(?:[ivxlcdm]+|\d+)\b(?:\s*[\.\:\-–—_]*\s*.*)?\s*$",
    re.IGNORECASE,
)

DISALLOWED_STRUCTURE_RE = re.compile(
    r"^\s*(?:book|part|letter)\s+(?:[ivxlcdm]+|\d+)\b(?:\s*[\.\:\-–—_]*\s*.*)?\s*$",
    re.IGNORECASE,
)


def read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def normalize_closing_line(line: str) -> str:
    cleaned = re.sub(r"[_=*~\-–—#.`'\":;,\[\]\(\)\{\}|\\/<>]+", " ", line)
    return normalize_spaces(cleaned).lower()


def relative_position(idx: int, total_lines: int) -> float:
    if total_lines <= 1:
        return 0.0
    return idx / (total_lines - 1)


def looks_like_chapter_i_opening(line: str) -> bool:
    return CHAPTER_I_OPENING_RE.match(line.strip()) is not None


def looks_like_chapter_entry(line: str) -> bool:
    return CHAPTER_ENTRY_RE.match(line.strip()) is not None


def looks_like_disallowed_structure(line: str) -> bool:
    return DISALLOWED_STRUCTURE_RE.match(line.strip()) is not None


def has_disallowed_structure(lines: list[str]) -> bool:
    for line in lines:
        if looks_like_disallowed_structure(line):
            return True
    return False


def next_nonempty_indices(lines: list[str], start_idx: int, limit: int) -> list[int]:
    indices: list[int] = []

    for i in range(start_idx + 1, len(lines)):
        if lines[i].strip():
            indices.append(i)
            if len(indices) >= limit:
                break

    return indices


def chapter_entry_count_after(
    lines: list[str],
    opening_idx: int,
    window: int = TOC_WINDOW_NONEMPTY_LINES,
) -> int:
    count = 0

    for idx in next_nonempty_indices(lines, opening_idx, window):
        if looks_like_chapter_entry(lines[idx]):
            count += 1

    return count


def is_toc_opening(
    lines: list[str],
    opening_idx: int,
    window: int = TOC_WINDOW_NONEMPTY_LINES,
    min_count: int = TOC_MIN_CHAPTER_ENTRY_COUNT,
) -> bool:
    return chapter_entry_count_after(lines, opening_idx, window) >= min_count


def is_valid_opening_position(idx: int, total_lines: int) -> bool:
    rel = relative_position(idx, total_lines)
    return OPENING_MIN_RELATIVE_POSITION <= rel <= OPENING_MAX_RELATIVE_POSITION


def find_opening_anchor(lines: list[str]) -> tuple[Optional[int], str]:
    if has_disallowed_structure(lines):
        return None, "has_disallowed_structure"

    chapter_i_indices: list[int] = []

    for i, line in enumerate(lines):
        if looks_like_chapter_i_opening(line) and is_valid_opening_position(i, len(lines)):
            chapter_i_indices.append(i)

    if not chapter_i_indices:
        return None, "no_valid_opening"

    valid_openings: list[int] = []

    for idx in chapter_i_indices:
        if not is_toc_opening(lines, idx):
            valid_openings.append(idx)

    if not valid_openings:
        return None, "only_toc_openings"

    if len(valid_openings) > 1:
        return None, "too_many_openings"

    return valid_openings[0], "ok"


def is_valid_closing_anchor(lines: list[str], idx: int) -> bool:
    if normalize_closing_line(lines[idx]) != "the end":
        return False

    rel = relative_position(idx, len(lines))
    return rel >= CLOSING_MIN_RELATIVE_POSITION


def find_closing_anchor(lines: list[str], start_idx: int) -> tuple[Optional[int], str]:
    match_indices: list[int] = []

    for i in range(start_idx, len(lines)):
        if is_valid_closing_anchor(lines, i):
            match_indices.append(i)

    if not match_indices:
        return None, "no_valid_closing"

    return match_indices[-1], "ok"


def bound_text(text: str) -> tuple[Optional[str], str]:
    lines = text.splitlines()

    if not lines:
        return None, "empty_file"

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
    text = read_text_safe(input_path)

    bounded, status = bound_text(text)
    if bounded is None:
        return status

    output_path.write_text(bounded, encoding="utf-8")
    return status