# Narrative Emotion Network

This project extracts and analyzes emotional relationships between characters in narrative texts.

The goal is to build character interaction graphs enriched with emotional context extracted from the story.

## Dataset

This project uses texts from Project Gutenberg.

Project Gutenberg is a digital library of public domain books, including novels, short stories, and other literary works.

Dataset source:  
https://www.gutenberg.org/

The texts are stored locally in the `data/gutenberg` folder and are not included in the repository.

To automatically download and clean the selected books, run:

```bash
python scripts/download_gutenberg.py
```

## Features

- Character detection
- Interaction extraction
- Emotion detection
- Narrative graph construction
- Graph analysis and visualization

## Planned pipeline

Text → Character detection → Interaction extraction → Emotion detection → Graph construction → Analysis

## Technologies

- Python
- spaCy
- NetworkX
- pandas