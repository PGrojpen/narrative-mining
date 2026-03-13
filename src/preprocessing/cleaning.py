import re
from pathlib import Path


SCENE_BREAK_RE = re.compile(r"^\s*(\*[\*\s]*|-{3,}|_{3,})\s*$")
CHAPTER_RE = re.compile(r"^(chapter|book|part)\s+([ivxlcdm]+|\d+)\b.*$", re.IGNORECASE)
ABBREVIATION_RE = re.compile(r"""(?ix)\b( mr|mrs|ms|dr|rev|st|prof|capt|col|gen|lt|sgt|jr|sr|messrs)\.$|\b[A-Z]\.$""")
INITIAL_RE = re.compile(r"\b[A-Z]\.$")
CAPITALIZED_WORD_RE = re.compile(r"^[A-Z][a-z]+(?:[-'][A-Za-z]+)?")
EDITORIAL_BRACKET_LINE_RE = re.compile(r"^\[\s*(.*?)\s*\]$")
TRAILING_PUNCT_RE = re.compile(r"[.:;,\-–—!?]+$")

def read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def normalize_line(line: str) -> str:
    line = line.replace("\t", " ")
    line = re.sub(r" +", " ", line)
    return line.strip()


def normalize_editorial_bracket_content(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = TRAILING_PUNCT_RE.sub("", text)
    return text


def is_editorial_bracket_line(line: str) -> bool:
    match = EDITORIAL_BRACKET_LINE_RE.fullmatch(line.strip())
    if not match:
        return False

    content = normalize_editorial_bracket_content(match.group(1))

    if not content:
        return False

    if content in {
        "illustration",
        "blank page",
        "the end",
    }:
        return True

    if content.startswith("illustration:"):
        return True

    return False


def is_scene_break(line: str) -> bool:
    return bool(SCENE_BREAK_RE.fullmatch(line))


def normalize_scene_break(line: str) -> str:
    if is_scene_break(line):
        return "***"
    return line


def looks_like_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False

    return bool(CHAPTER_RE.fullmatch(stripped))


def ends_sentence(line: str) -> bool:
    return bool(re.search(r'[.!?]["\')\]]*$', line.rstrip()))


def starts_obvious_new_block(line: str) -> bool:
    stripped = line.lstrip()

    if not stripped:
        return False

    if looks_like_heading(stripped):
        return True

    if is_scene_break(stripped):
        return True

    if stripped.startswith(("—", '"', "'")):
        return True

    return False


def is_hyphenated_word_break(current: str, next_line: str) -> bool:
    left = current.rstrip()
    right = next_line.lstrip()

    if not left or not right:
        return False

    return bool(
        re.search(r"[A-Za-z]-$", left)
        and re.match(r"^[a-z]", right)
    )



def ends_with_protected_abbreviation(line: str) -> bool:
    stripped = line.strip()
    return bool(ABBREVIATION_RE.search(stripped))


def ends_with_name_initial(line: str) -> bool:
    stripped = line.strip()
    return bool(INITIAL_RE.search(stripped))


def starts_with_capitalized_word(line: str) -> bool:
    stripped = line.lstrip()
    return bool(CAPITALIZED_WORD_RE.match(stripped))


def should_merge(current: str, next_line: str) -> bool:
    if not current.strip() or not next_line.strip():
        return False

    if looks_like_heading(current):
        return False

    if ends_with_protected_abbreviation(current) and starts_with_capitalized_word(next_line):
        return True

    if ends_with_name_initial(current) and starts_with_capitalized_word(next_line):
        return True

    if starts_obvious_new_block(next_line):
        return False

    if ends_sentence(current):
        return False

    return True

def preprocess_lines(text: str) -> list[str]:
    lines = []

    for line in text.split("\n"):
        line = normalize_line(line)

        if is_editorial_bracket_line(line):
            line = ""

        line = normalize_scene_break(line)
        lines.append(line)

    return lines


def merge_lines(lines: list[str]) -> tuple[list[str], dict[str, int]]:
    merged = []
    i = 0

    stats = {
        "line_merges": 0,
        "hyphen_merges": 0,
    }

    while i < len(lines):
        current = lines[i]

        if not current:
            merged.append("")
            i += 1
            continue

        if is_scene_break(current):
            merged.append(current)
            i += 1
            continue

        while i + 1 < len(lines):
            next_line = lines[i + 1]

            if not next_line:
                break

            if is_hyphenated_word_break(current, next_line):
                current = current[:-1] + next_line.lstrip()
                i += 1
                stats["hyphen_merges"] += 1
                continue

            if should_merge(current, next_line):
                current = current.rstrip() + " " + next_line.lstrip()
                i += 1
                stats["line_merges"] += 1
                continue

            break

        merged.append(current)
        i += 1

    return merged, stats


def collapse_blank_lines(lines: list[str]) -> list[str]:
    result = []
    previous_blank = False

    for line in lines:
        if not line:
            if not previous_blank:
                result.append("")
            previous_blank = True
        else:
            result.append(line)
            previous_blank = False

    return result


def count_blank_lines(lines: list[str]) -> int:
    return sum(1 for line in lines if not line)


def count_scene_breaks(lines: list[str]) -> int:
    return sum(1 for line in lines if line == "***")


def clean_text(text: str) -> tuple[str, dict[str, int]]:
    original_text = text
    text = normalize_newlines(text)

    preprocessed_lines = preprocess_lines(text)
    merged_lines, merge_stats = merge_lines(preprocessed_lines)
    cleaned_lines = collapse_blank_lines(merged_lines)
    cleaned_text = "\n".join(cleaned_lines).strip() + "\n"

    normalized_original = normalize_newlines(original_text).strip() + "\n"

    stats = {
        "changed": int(cleaned_text != normalized_original),
        "raw_line_count": len(preprocessed_lines),
        "cleaned_line_count": len(cleaned_lines),
        "raw_blank_lines": count_blank_lines(preprocessed_lines),
        "cleaned_blank_lines": count_blank_lines(cleaned_lines),
        "raw_scene_breaks": count_scene_breaks(preprocessed_lines),
        "cleaned_scene_breaks": count_scene_breaks(cleaned_lines),
        "line_merges": merge_stats["line_merges"],
        "hyphen_merges": merge_stats["hyphen_merges"],
    }

    return cleaned_text, stats


def clean_file(input_path: Path, output_path: Path) -> dict[str, int]:
    text = read_text_safe(input_path)
    cleaned, stats = clean_text(text)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(cleaned, encoding="utf-8")

    return stats