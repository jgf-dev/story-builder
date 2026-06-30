"""Extract Named Entities from stories using spaCy."""

import argparse
import sqlite3
from collections import Counter
from pathlib import Path

import spacy
from thinc.api import require_gpu, set_gpu_allocator
from tqdm import tqdm

DB_PATH = "nlp_analysis.db"
ALLOWED_LABELS = {
    "PERSON",
    "NORP",
    "GPE",
    "LOC",
    "ORG",
    "FAC",
    "EVENT",
    "PRODUCT",
    "WORK_OF_ART",
}


def init_db(db_path):
    """Initialize the SQLite database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath TEXT UNIQUE,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER,
            text TEXT,
            label TEXT,
            frequency INTEGER,
            FOREIGN KEY(story_id) REFERENCES stories(id)
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_label ON entities(label)")

    conn.commit()
    return conn


def is_processed(cursor, filepath):
    """Check if a file has already been processed."""
    cursor.execute("SELECT id FROM stories WHERE filepath = ?", (filepath,))
    return cursor.fetchone() is not None


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract Named Entities from stories using spaCy."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=float("inf"),
        help="Maximum number of new files to process.",
    )
    parser.add_argument(
        "--stories-dir",
        type=str,
        default="nifty_stories",
        help="Directory containing the text files.",
    )
    parser.add_argument(
        "--db-path", type=str, default=DB_PATH, help="Path to the SQLite database."
    )
    parser.add_argument(
        "--force", action="store_true", help="Force reprocessing of all files."
    )
    parser.add_argument(
        "--model", type=str, default="en_core_web_lg", help="spaCy model to use."
    )
    parser.add_argument(
        "--gpu", action="store_true", default=True, help="Use GPU for spaCy model."
    )
    return parser.parse_args()


def load_spacy_model(model_name, use_gpu):
    """Load the spaCy model with optional GPU support."""
    try:
        if use_gpu:
            set_gpu_allocator("pytorch")
            require_gpu(0)
            spacy.require_gpu()
            nlp = spacy.load(model_name)
        else:
            nlp = spacy.load(model_name)

        nlp.select_pipes(enable=["tagger", "parser", "ner"])
        nlp.add_pipe("merge_noun_chunks")
        nlp.add_pipe("merge_entities")
        nlp.max_length = 5000000
        return nlp
    except OSError:
        print(f"Model '{model_name}' not found.")
        print(f"Please run: python -m spacy download {model_name}")
        return None


def process_file(filepath_str, nlp, cursor):
    """Extract entities from a text file and save them to the database."""
    with open(filepath_str, "r", encoding="utf-8") as f:
        text = f.read()

    doc = nlp(text)
    entities = Counter(
        (ent.text.strip(), ent.label_)
        for ent in doc.ents
        if ent.label_ in ALLOWED_LABELS and ent.text.strip()
    )

    query = "INSERT INTO stories (filepath) VALUES (?)"
    cursor.execute(query, (filepath_str,))
    story_id = cursor.lastrowid

    entity_records = [
        (story_id, ent_text, label, count)
        for (ent_text, label), count in entities.items()
    ]

    cursor.executemany(
        """
        INSERT INTO entities (story_id, text, label, frequency)
        VALUES (?, ?, ?, ?)
    """,
        entity_records,
    )


def main():
    """Main execution block."""
    args = parse_args()

    print("Initializing database...")
    conn = init_db(args.db_path)
    cursor = conn.cursor()
    if args.force:
        cursor.execute("DELETE FROM stories")
        cursor.execute("DELETE FROM entities")
        conn.commit()

    print(f"Loading spaCy model ({args.model})...")
    nlp = load_spacy_model(args.model, args.gpu)
    if nlp is None:
        conn.close()
        # Signal failure so CI pipelines and scripts that check the exit code
        # treat a missing/unloadable model as an error rather than success.
        raise SystemExit(1)
    all_files = list(Path(args.stories_dir).rglob("*.txt"))
    print(f"Found {len(all_files)} total text files.")

    processed_count = 0
    pbar = tqdm(total=min(len(all_files), args.limit), desc="Processing files")

    for filepath in all_files:
        filepath_str = str(filepath)

        if not args.force and is_processed(cursor, filepath_str):
            continue

        try:
            process_file(filepath_str, nlp, cursor)
            conn.commit()

            processed_count += 1
            pbar.update(1)

            if processed_count >= args.limit:
                break

        except Exception as e:  # pylint: disable=broad-except
            print(f"\nError processing {filepath_str}: {e}")
            conn.rollback()

    pbar.close()
    conn.close()
    print(f"\nFinished! Processed {processed_count} new files.")


if __name__ == "__main__":
    main()
