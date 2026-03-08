from pathlib import Path
from tqdm import tqdm
from src.config import TARGET_COUNT, SEED

RAW_DIR = Path("data/gutenberg/raw")
OUTPUT_FILE = Path(f"data/gutenberg/inspection/book_edges_{TARGET_COUNT}_seed{SEED}.txt")

BEGINNING_LINES = 50
END_LINES = 50


def read_lines(file_path: Path) -> list[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.readlines()


def format_block(title: str, lines: list[str], start_index: int = 1) -> str:
    formatted_lines = [f"{i:02d}: {line.rstrip()}" for i, line in enumerate(lines, start=start_index)]
    return f"{title}\n" + "\n".join(formatted_lines)


def build_file_report(file_path: Path) -> str:
    lines = read_lines(file_path)
    total_lines = len(lines)

    beginning = lines[:BEGINNING_LINES]
    ending = lines[-END_LINES:] if total_lines > END_LINES else lines

    beginning_block = format_block("--- BEGINNING ---", beginning, start_index=1)

    ending_start_index = total_lines - len(ending) + 1
    ending_block = format_block("--- END ---", ending, start_index=ending_start_index)

    return (
        f"{'=' * 80}\n"
        f"FILE: {file_path.name}\n"
        f"TOTAL LINES: {total_lines}\n"
        f"{'=' * 80}\n\n"
        f"{beginning_block}\n\n"
        f"{ending_block}\n\n"
    )


def main() -> None:
    txt_files = sorted(RAW_DIR.glob("*.txt"))

    if not txt_files:
        print(f"Nenhum arquivo .txt encontrado em {RAW_DIR}")
        return

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    reports = []
    failed = 0

    with tqdm(txt_files, desc="Building book edges", unit="book") as pbar:
        for file_path in pbar:
            try:
                reports.append(build_file_report(file_path))
            except Exception as e:
                failed += 1
                tqdm.write(f"Failed: {file_path.name} -> {e}")

            pbar.set_postfix(failed=failed)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(reports))

    print(f"\nArquivo salvo em: {OUTPUT_FILE}")
    print(f"Livros processados: {len(reports)}")
    print(f"Falhas: {failed}")


if __name__ == "__main__":
    main()