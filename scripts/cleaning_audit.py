import random
from difflib import unified_diff
from pathlib import Path

from config import BOUNDED_PATH, CLEANED_PATH, TESTS_PATH, SEED

SAMPLE_SIZE = 10


def read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def get_common_files() -> list[str]:
    bounded_names = {
        path.name
        for path in BOUNDED_PATH.glob("*.txt")
        if path.is_file()
    }
    cleaned_names = {
        path.name
        for path in CLEANED_PATH.glob("*.txt")
        if path.is_file()
    }
    return sorted(bounded_names & cleaned_names)


def build_diff(file_name: str, bounded_text: str, cleaned_text: str) -> str:
    bounded_lines = bounded_text.splitlines(keepends=True)
    cleaned_lines = cleaned_text.splitlines(keepends=True)

    diff_lines = unified_diff(
        bounded_lines,
        cleaned_lines,
        fromfile=f"bounded/{file_name}",
        tofile=f"cleaned/{file_name}",
        lineterm="",
    )
    return "".join(diff_lines)


def main() -> None:
    random.seed(SEED)

    common_files = get_common_files()
    if not common_files:
        raise FileNotFoundError("No matching .txt files found in both bounded and cleaned.")

    sample_size = min(SAMPLE_SIZE, len(common_files))
    sample_names = random.sample(common_files, k=sample_size)

    output_dir = TESTS_PATH / "bounded_vs_cleaned_diff"
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_lines = [f"Compared files: {sample_size}", ""]

    for file_name in sorted(sample_names):
        bounded_text = read_text_safe(BOUNDED_PATH / file_name)
        cleaned_text = read_text_safe(CLEANED_PATH / file_name)

        diff_text = build_diff(file_name, bounded_text, cleaned_text)
        stem = Path(file_name).stem

        (output_dir / f"{stem}_diff.txt").write_text(
            diff_text if diff_text else "No differences found.\n",
            encoding="utf-8",
        )

        summary_lines.append(
            f"{file_name} | changed={'YES' if bounded_text != cleaned_text else 'NO'}"
        )

    (output_dir / "_summary.txt").write_text(
        "\n".join(summary_lines) + "\n",
        encoding="utf-8",
    )

    print(f"Diffs saved to: {output_dir}")
    print(f"Total compared: {sample_size}")


if __name__ == "__main__":
    main()