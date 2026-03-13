from pathlib import Path
import json

from config import TESTS_PATH
from src.preprocessing.cleaning import clean_text


def read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def write_json_if_missing(path: Path, data: dict) -> None:
    if not path.exists():
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def ensure_cleaning_cases(base: Path) -> None:
    base.mkdir(parents=True, exist_ok=True)

    cases = {
        "merge_plain_lines": {
            "input": "This is a line\nthat continues\nwithout ending punctuation.\n",
            "expected": "This is a line that continues without ending punctuation.\n",
            "stats": {
                "changed": 1,
                "line_merges": 2,
                "hyphen_merges": 0,
            },
        },
        "no_merge_after_sentence": {
            "input": "This is a complete sentence.\nThis should start a new line.\n",
            "expected": "This is a complete sentence.\nThis should start a new line.\n",
            "stats": {
                "changed": 0,
                "line_merges": 0,
                "hyphen_merges": 0,
            },
        },
        "normalize_spaces_tabs": {
            "input": "This\thas   extra\tspaces\nand    tabs.\n",
            "expected": "This has extra spaces and tabs.\n",
            "stats": {
                "changed": 1,
                "line_merges": 1,
                "hyphen_merges": 0,
            },
        },
        "scene_break_stars": {
            "input": "* * *\n\nNext scene starts here.\n",
            "expected": "***\n\nNext scene starts here.\n",
            "stats": {
                "changed": 1,
                "raw_scene_breaks": 1,
                "cleaned_scene_breaks": 1,
            },
        },
        "scene_break_dashes": {
            "input": "---\nA new scene after dashes.\n",
            "expected": "***\nA new scene after dashes.\n",
            "stats": {
                "changed": 1,
                "raw_scene_breaks": 1,
                "cleaned_scene_breaks": 1,
            },
        },
        "scene_break_underscores": {
            "input": "___\nAnother new scene.\n",
            "expected": "***\nAnother new scene.\n",
            "stats": {
                "changed": 1,
                "raw_scene_breaks": 1,
                "cleaned_scene_breaks": 1,
            },
        },
        "hyphen_merge": {
            "input": "infor-\nmation is important.\n",
            "expected": "information is important.\n",
            "stats": {
                "changed": 1,
                "line_merges": 0,
                "hyphen_merges": 1,
            },
        },
        "preserve_paragraph_break": {
            "input": "This is a line\n\nthat starts a new paragraph.\n",
            "expected": "This is a line\n\nthat starts a new paragraph.\n",
            "stats": {
                "changed": 0,
                "line_merges": 0,
                "hyphen_merges": 0,
            },
        },
        "collapse_blank_lines": {
            "input": "This is a line\n\n\nthat has too many blank lines.\n",
            "expected": "This is a line\n\nthat has too many blank lines.\n",
            "stats": {
                "changed": 1,
            },
        },
        "no_merge_dialogue_quote": {
            "input": 'This line introduces dialogue\n"Hello," she said.\n',
            "expected": 'This line introduces dialogue\n"Hello," she said.\n',
            "stats": {
                "changed": 0,
                "line_merges": 0,
            },
        },
        "no_merge_dialogue_dash": {
            "input": "He was about to answer\n— when the door opened.\n",
            "expected": "He was about to answer\n— when the door opened.\n",
            "stats": {
                "changed": 0,
                "line_merges": 0,
            },
        },
        "heading_chapter": {
            "input": "Chapter I\nThe Beginning\n",
            "expected": "Chapter I\nThe Beginning\n",
            "stats": {
                "changed": 0,
                "line_merges": 0,
            },
        },
        "heading_with_blank_after": {
            "input": "Chapter I\n\nThe Beginning\n",
            "expected": "Chapter I\n\nThe Beginning\n",
            "stats": {
                "changed": 0,
                "line_merges": 0,
            },
        },
        "heading_part": {
            "input": "Part II\nThe road continued into darkness.\n",
            "expected": "Part II\nThe road continued into darkness.\n",
            "stats": {
                "changed": 0,
                "line_merges": 0,
            },
        },
        "heading_book": {
            "input": "Book III\nA storm was coming.\n",
            "expected": "Book III\nA storm was coming.\n",
            "stats": {
                "changed": 0,
                "line_merges": 0,
            },
        },
        "not_a_heading": {
            "input": "This is not a heading called chapter house\nit should merge normally\n",
            "expected": "This is not a heading called chapter house it should merge normally\n",
            "stats": {
                "changed": 1,
                "line_merges": 1,
            },
        },
        "sentence_endings": {
            "input": "He stopped!\nWhy was she still there?\n",
            "expected": "He stopped!\nWhy was she still there?\n",
            "stats": {
                "changed": 0,
                "line_merges": 0,
            },
        },
        "odd_quote_still_merges": {
            "input": 'She whispered,"\nsoftly into the dark.\n',
            "expected": 'She whispered," softly into the dark.\n',
            "stats": {
                "changed": 1,
                "line_merges": 1,
            },
        },
        "merge_and_scene_break": {
            "input": "The old man walked slowly\nthrough the empty field\n\n* * *\n\nNothing moved after that.\n",
            "expected": "The old man walked slowly through the empty field\n\n***\n\nNothing moved after that.\n",
            "stats": {
                "changed": 1,
                "line_merges": 1,
                "hyphen_merges": 0,
                "raw_scene_breaks": 1,
                "cleaned_scene_breaks": 1,
            },
        },
        "multiple_behaviors": {
            "input": "This is a line\nthat continues.\n\n\nAnother paragraph starts\nand also continues\nfor one more line.\n",
            "expected": "This is a line that continues.\n\nAnother paragraph starts and also continues for one more line.\n",
            "stats": {
                "changed": 1,
                "line_merges": 3,
                "hyphen_merges": 0,
            },
        },
    }

    created = 0

    for case_id, data in cases.items():
        input_path = base / f"{case_id}_input.txt"
        expected_path = base / f"{case_id}_expected.txt"
        stats_path = base / f"{case_id}_stats.json"

        existed_before = (
            input_path.exists()
            and expected_path.exists()
            and stats_path.exists()
        )

        write_if_missing(input_path, data["input"])
        write_if_missing(expected_path, data["expected"])
        write_json_if_missing(stats_path, data["stats"])

        if not existed_before:
            created += 1

    print(f"Cases ensured in: {base}")
    print(f"New cases created: {created}")


def run_cleaning_cases(base: Path) -> None:
    input_files = sorted(base.glob("*_input.txt"))

    if not input_files:
        raise FileNotFoundError(f"No input cases found in {base}")

    for input_path in input_files:
        case_id = input_path.stem.removesuffix("_input")
        expected_path = base / f"{case_id}_expected.txt"
        stats_path = base / f"{case_id}_stats.json"

        if not expected_path.exists():
            raise FileNotFoundError(f"Missing expected file for case: {case_id}")

        if not stats_path.exists():
            raise FileNotFoundError(f"Missing stats json for case: {case_id}")

        raw_text = read_text_safe(input_path)
        expected_text = read_text_safe(expected_path)
        expected_stats = json.loads(stats_path.read_text(encoding="utf-8"))

        actual_text, actual_stats = clean_text(raw_text)

        assert actual_text == expected_text, (
            f"[TEXT FAIL] {case_id}\n\n"
            f"EXPECTED:\n{repr(expected_text)}\n\n"
            f"ACTUAL:\n{repr(actual_text)}"
        )

        for key, expected_value in expected_stats.items():
            actual_value = actual_stats.get(key)
            assert actual_value == expected_value, (
                f"[STATS FAIL] {case_id} | {key}\n"
                f"expected={expected_value} actual={actual_value}"
            )

        print(f"[PASS] {case_id}")

    print("\nAll cleaning cases passed.")


def main() -> None:
    base = TESTS_PATH / "cleaning_cases"
    ensure_cleaning_cases(base)
    run_cleaning_cases(base)


if __name__ == "__main__":
    main()
