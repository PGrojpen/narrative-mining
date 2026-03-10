from pathlib import Path

from config import RAW_PATH, PRE_CLEANED_PATH
from src.preprocessing.pre_cleaning import pre_clean_file, pre_clean_all_files


def main() -> None:

    sample_file = RAW_PATH / "53769.txt"

    PRE_CLEANED_PATH.mkdir(parents=True, exist_ok=True)
    pre_clean_file(sample_file.name)

    output_path = PRE_CLEANED_PATH / sample_file.name

    print(f"File tested: {sample_file.name}")
    print(f"Output generated: {output_path}")
    print("Smoke test passed.")

    pre_clean_all_files()


if __name__ == "__main__":
    main()