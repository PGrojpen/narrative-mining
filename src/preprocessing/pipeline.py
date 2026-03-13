from pathlib import Path

from tqdm import tqdm

from config import RAW_PATH, BOUNDED_PATH
from src.preprocessing.boundary_detection import process_file


from collections import Counter, defaultdict

from tqdm import tqdm


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


if __name__ == "__main__":
    run_boundary_detection()