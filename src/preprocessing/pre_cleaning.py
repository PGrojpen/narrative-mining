import re
from tqdm import tqdm
from pathlib import Path

from config import RAW_PATH, PRE_CLEANED_PATH


SEPARATOR_PATTERN = re.compile(r"^\s*([\-_=*~])(\s*\1){2,}\s*$")


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def remove_bom(text: str) -> str:
    return text.lstrip("\ufeff")


def replace_tabs(text: str) -> str:
    return text.replace("\t", " ")


def normalize_inline_spaces(line: str) -> str:
    return re.sub(r"[ ]{2,}", " ", line).strip()


def remove_obvious_separator_lines(lines: list[str]) -> list[str]:
    cleaned: list[str] = []

    for line in lines:
        if SEPARATOR_PATTERN.match(line):
            cleaned.append("")
        else:
            cleaned.append(line)

    return cleaned


def collapse_multiple_blank_lines(lines: list[str], max_blank: int = 2) -> list[str]:
    cleaned: list[str] = []
    blank_count = 0

    for line in lines:
        if not line.strip():
            blank_count += 1
            if blank_count <= max_blank:
                cleaned.append("")
        else:
            blank_count = 0
            cleaned.append(line)

    return cleaned


def pre_clean_text(text: str) -> str:
    text = normalize_newlines(text)
    text = remove_bom(text)
    text = replace_tabs(text)

    lines = text.split("\n")
    lines = [normalize_inline_spaces(line) for line in lines]
    lines = remove_obvious_separator_lines(lines)
    lines = collapse_multiple_blank_lines(lines, max_blank=2)

    return "\n".join(lines).strip() + "\n"


def pre_clean_file(file_name: str) -> None:
    input_path = RAW_PATH / file_name
    output_path = PRE_CLEANED_PATH / file_name

    text = input_path.read_text(encoding="utf-8", errors="replace")
    cleaned = pre_clean_text(text)

    output_path.write_text(cleaned, encoding="utf-8")

def pre_clean_all_files() -> None:
    PRE_CLEANED_PATH.mkdir(parents=True, exist_ok=True)

    txt_files = sorted(RAW_PATH.glob("*.txt"))
    if not txt_files:
        print(f"Nenhum arquivo .txt encontrado em: {RAW_PATH}")
        return

    for input_path in tqdm(txt_files, desc="Pre-cleaning books", unit="book"):
        pre_clean_file(input_path.name)

    print(f"Total processado: {len(txt_files)} arquivo(s)")
    print(f"Saída salva em: {PRE_CLEANED_PATH}")