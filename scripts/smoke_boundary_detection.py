from pathlib import Path

from src.preprocessing.boundary_detection import bound_text


SAMPLE_FILE = Path("data/gutenberg/raw/43120.txt")


def preview_start(text: str, n: int = 1200) -> str:
    return text[:n]


def preview_end(text: str, n: int = 1200) -> str:
    return text[-n:]


def main() -> None:
    text = SAMPLE_FILE.read_text(encoding="utf-8", errors="ignore")
    bounded, status = bound_text(text)

    if bounded is not None:
        print("=== ORIGINAL START ===")
        print(preview_start(bounded))
        print("\n=== ORIGINAL END ===")
        print(preview_end(text))

        print("\n=== BOUNDED START ===")
        print(preview_start(bounded))
        print("\n=== BOUNDED END ===")
        print(preview_end(bounded))

        print("Boundary smoke test passed.\n")

    else:
        print(status)



if __name__ == "__main__":
    main()