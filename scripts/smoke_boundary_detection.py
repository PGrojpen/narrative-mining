import random
from pathlib import Path

from src.preprocessing.boundary_detection import bound_text
from config import RAW_PATH,TESTS_PATH, SEED

SAMPLE_SIZE = 20

def get_book_files(folder: Path) -> list[Path]:
    return sorted(
        path for path in folder.glob("*.txt")
        if path.is_file()
    )


def preview_start(text: str, n: int = 1200) -> str:
    return text[:n]


def preview_end(text: str, n: int = 1200) -> str:
    return text[-n:]


def read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")
    

def main() -> None:
    random.seed(SEED)

    files = get_book_files(RAW_PATH)
    if not files:
        raise FileNotFoundError(f"No .txt files found in {RAW_PATH}")

    sample_size = min(SAMPLE_SIZE, len(files))
    sample_files = random.sample(files, k=sample_size)

    output_dir = TESTS_PATH / "bounded"
    output_dir.mkdir(parents=True, exist_ok=True)

    for sample_file in sample_files:
        text = read_text_safe(sample_file)
        bounded, status = bound_text(text)

        print("=" * 100)
        print(f"FILE: {sample_file.name}\n")

        if bounded is not None:
            (output_dir / sample_file.name).write_text(bounded, encoding="utf-8")

            print("=== ORIGINAL START ===")
            print(preview_start(text))

            print("\n=== ORIGINAL END ===")
            print(preview_end(text))

            print("\n=== BOUNDED START ===")
            print(preview_start(bounded))

            print("\n=== BOUNDED END ===")
            print(preview_end(bounded))

            print("\nBoundary smoke test passed.\n")
        else:
            print(f"BOUNDARY FAILED: {status}\n")


if __name__ == "__main__":
    main()