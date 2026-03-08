from pathlib import Path

from src.preprocessing.boundary_detection import detect_boundaries

SAMPLE_FILE = Path("data/gutenberg/raw/158.txt")

def smoke_test_boundary() -> None:
    text = SAMPLE_FILE.read_text(encoding="utf-8")
    bounded_text = detect_boundaries(text)

    assert isinstance(bounded_text, str)
    assert bounded_text.strip() != ""
    assert len(bounded_text) < len(text)

    print("Boundary smoke test passed.")
    print(f"Original length: {len(text)}")
    print(f"Bounded length: {len(bounded_text)}")

if __name__ == "__main__":
    smoke_test_boundary()