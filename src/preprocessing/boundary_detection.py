from pathlib import Path

from gutenberg_cleaner import simple_cleaner
from tqdm import tqdm


RAW_DIR = Path("data/gutenberg/raw")
BOUNDED_DIR = Path("data/gutenberg/processed/bounded")


def detect_boundaries(text: str) -> str:
    if not text or not text.strip():
        return ""
    return simple_cleaner(text).strip()


def process_file(input_path: Path, output_path: Path) -> None:
    text = input_path.read_text(encoding="utf-8")
    bounded_text = detect_boundaries(text)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(bounded_text, encoding="utf-8")


def process_all_books(raw_dir: Path = RAW_DIR, bounded_dir: Path = BOUNDED_DIR) -> None:
    bounded_dir.mkdir(parents=True, exist_ok=True)

    input_files = sorted(raw_dir.glob("*.txt"))

    for input_path in tqdm(input_files, desc="Boundary detection", unit="book"):
        output_path = bounded_dir / input_path.name
        process_file(input_path, output_path)