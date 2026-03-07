import requests
import time
from pathlib import Path
from tqdm import tqdm

BOOKS = [
    {"id": 1342, "title": "pride_and_prejudice", "author": "jane_austen"},
    {"id": 161, "title": "sense_and_sensibility", "author": "jane_austen"},
    {"id": 158, "title": "emma", "author": "jane_austen"},
    {"id": 105, "title": "persuasion", "author": "jane_austen"},
    {"id": 84, "title": "frankenstein", "author": "mary_shelley"},
    {"id": 345, "title": "dracula", "author": "bram_stoker"},
    {"id": 174, "title": "the_picture_of_dorian_gray", "author": "oscar_wilde"},
    {"id": 1260, "title": "jane_eyre", "author": "charlotte_bronte"},
    {"id": 768, "title": "wuthering_heights", "author": "emily_bronte"},
    {"id": 98, "title": "a_tale_of_two_cities", "author": "charles_dickens"},
    {"id": 730, "title": "oliver_twist", "author": "charles_dickens"},
    {"id": 1400, "title": "great_expectations", "author": "charles_dickens"},
    {"id": 1661, "title": "the_adventures_of_sherlock_holmes", "author": "arthur_conan_doyle"},
    {"id": 2852, "title": "the_hound_of_the_baskervilles", "author": "arthur_conan_doyle"},
    {"id": 244, "title": "a_study_in_scarlet", "author": "arthur_conan_doyle"},
    {"id": 120, "title": "treasure_island", "author": "robert_louis_stevenson"},
    {"id": 43, "title": "dr_jekyll_and_mr_hyde", "author": "robert_louis_stevenson"},
    {"id": 74, "title": "the_adventures_of_tom_sawyer", "author": "mark_twain"},
    {"id": 76, "title": "adventures_of_huckleberry_finn", "author": "mark_twain"},
    {"id": 2701, "title": "moby_dick", "author": "herman_melville"},
    {"id": 35, "title": "the_time_machine", "author": "h_g_wells"},
    {"id": 36, "title": "the_war_of_the_worlds", "author": "h_g_wells"},
    {"id": 5230, "title": "the_invisible_man", "author": "h_g_wells"},
    {"id": 155, "title": "the_moonstone", "author": "wilkie_collins"},
    {"id": 583, "title": "the_woman_in_white", "author": "wilkie_collins"},
]

SAVE_DIR = Path("data/gutenberg")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

def download_book(book_id):
    urls = [
        f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt",
    ]

    for url in urls:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                return r.text
        except requests.RequestException:
            pass

    return None

def clean_gutenberg(text):

    start_marker = "*** START OF"
    end_marker = "*** END OF"

    start = text.find(start_marker)
    end = text.find(end_marker)

    if start != -1 and end != -1:
        text = text[start:end]

    lines = text.splitlines()

    # remove a primeira linha (marcador)
    lines = lines[1:]

    return "\n".join(lines).strip()

def main():

    for book in tqdm(BOOKS, desc="Downloading books"):

        book_id = book["id"]
        title = book["title"]

        text = download_book(book_id)

        if text is None:
            print(f"Failed to download {book_id}")
            continue

        cleaned = clean_gutenberg(text)

        path = SAVE_DIR / f"{title}.txt"

        with open(path, "w", encoding="utf-8") as f:
            f.write(cleaned)

        time.sleep(1)


if __name__ == "__main__":
    main()