import json
from pathlib import Path

from tqdm import tqdm

from config import RAW_PATH, METADATA_PATH, BOUNDED_PATH, CLEANED_PATH
from src.preprocessing.metadata_extraction import load_selected_metadata
from src.preprocessing.boundary_detection import process_file
from src.preprocessing.cleaning import clean_file

from collections import Counter, defaultdict

from tqdm import tqdm


def run_metadata_extraction() -> None:
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    metadata = load_selected_metadata(books_folder=RAW_PATH)

    with open(METADATA_PATH/"metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("\nMETADATA EXTRACTION FINISHED")
    print(f"Books with metadata: {len(metadata)}")
    print(f"Saved to:            {METADATA_PATH}")


def run_boundary_detection() -> None:
    BOUNDED_PATH.mkdir(parents=True, exist_ok=True)

    input_files = sorted(RAW_PATH.glob("*.txt"))
    stats = Counter()
    discarded_files = defaultdict(list)
    
    for input_path in tqdm(input_files, desc="Boundary detection"):
        output_path = BOUNDED_PATH / input_path.name

        if output_path.exists():
            stats["skipped"] += 1
            continue

        status = process_file(input_path, output_path)

        stats[status] += 1

        if status != "saved":
            discarded_files[status].append(input_path.name)

    print("\nBOUNDARY DETECTION FINISHED")
    print(f"Input files: {len(input_files)}")
    print(f"Saved:       {stats['saved']}")
    print(f"Skipped:     {stats['skipped']}")
    discarded = len(input_files) - stats["saved"] - stats["skipped"]

    discard_reasons = {
        key: value
        for key, value in stats.items()
        if key not in {"saved", "skipped"}
    }

    if discard_reasons:
        print("\nDiscard reasons:")
        for reason, count in sorted(discard_reasons.items(), key=lambda item: item[1], reverse=True):
            print(f"{reason}: {count}")


def run_cleaning() -> None:
    CLEANED_PATH.mkdir(parents=True, exist_ok=True)

    input_files = sorted(BOUNDED_PATH.glob("*.txt"))
    stats = Counter()

    for input_path in tqdm(input_files, desc="Cleaning"):
        output_path = CLEANED_PATH / input_path.name

        if output_path.exists():
            stats["skipped"] += 1
            continue

        file_stats = clean_file(input_path, output_path)

        stats["saved"] += 1
        stats["changed"] += file_stats["changed"]
        stats["unchanged"] += 1 - file_stats["changed"]
        stats["raw_line_count"] += file_stats["raw_line_count"]
        stats["cleaned_line_count"] += file_stats["cleaned_line_count"]
        stats["raw_blank_lines"] += file_stats["raw_blank_lines"]
        stats["cleaned_blank_lines"] += file_stats["cleaned_blank_lines"]
        stats["raw_scene_breaks"] += file_stats["raw_scene_breaks"]
        stats["cleaned_scene_breaks"] += file_stats["cleaned_scene_breaks"]
        stats["line_merges"] += file_stats["line_merges"]
        stats["hyphen_merges"] += file_stats["hyphen_merges"]

    print("\nCLEANING FINISHED")
    print(f"Input files:          {len(input_files)}")
    print(f"Saved:                {stats['saved']}")
    print(f"Skipped:              {stats['skipped']}")
    print(f"Changed files:        {stats['changed']}")
    print(f"Unchanged files:      {stats['unchanged']}")
    print(f"Raw line count:       {stats['raw_line_count']}")
    print(f"Cleaned line count:   {stats['cleaned_line_count']}")
    print(f"Raw blank lines:      {stats['raw_blank_lines']}")
    print(f"Cleaned blank lines:  {stats['cleaned_blank_lines']}")
    print(f"Raw scene breaks:     {stats['raw_scene_breaks']}")
    print(f"Cleaned scene breaks: {stats['cleaned_scene_breaks']}")
    print(f"Line merges:          {stats['line_merges']}")
    print(f"Hyphen merges:        {stats['hyphen_merges']}")


if __name__ == "__main__":
    run_metadata_extraction()
    run_boundary_detection()
    run_cleaning()