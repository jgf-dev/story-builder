import argparse
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

import spacy
from thinc.api import require_gpu
from thinc.api import set_gpu_allocator
from tqdm import tqdm
from transformers import pipeline


DB_PATH = "sentiment_analysis.db"
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
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_dir TEXT UNIQUE,
            subcategory TEXT
        )
    """,
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sentences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER,
            chapter_filename TEXT,
            chapter_index INTEGER,
            sentence_index INTEGER,
            text TEXT,
            sentiment_score REAL,
            FOREIGN KEY(story_id) REFERENCES stories(id)
        )
    """,
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sentence_entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sentence_id INTEGER,
            entity_text TEXT,
            entity_label TEXT,
            FOREIGN KEY(sentence_id) REFERENCES sentences(id)
        )
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> palette/fix-duplicate-file-input-14315194890274537724
    """
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_sentences_story ON sentences(story_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_entities_sentence ON sentence_entities(sentence_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_entities_text ON sentence_entities(entity_text)"
=======
    """,
>>>>>>> palette-fix-duplicate-file-input-1065389564287363483
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sentences_story ON sentences(story_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_sentence ON sentence_entities(sentence_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_text ON sentence_entities(entity_text)")

    conn.commit()
    return conn


def get_sentiment_value(result):
    label = result["label"].lower()
    score = result["score"]
    if "positive" in label:
        return score
    if "negative" in label:
        return -score
    return 0.0


def extract_chapter_number(filename):
    """Attempts to extract a chapter number from a filename like 'story-name-12.txt'."""
    match = re.search(r"-(\d+)\.txt$", filename)
    if match:
        return int(match.group(1))

    match = re.search(r"(\d+)", filename)
    if match:
        return int(match.group(1))

    return 0


def parse_args():
    parser = argparse.ArgumentParser(description="Analyze narrative sentiment and entity interactions.")
    parser.add_argument(
        "--stories-dir",
        type=str,
        default="test_stories",
        help="Directory containing stories.",
    )
    parser.add_argument(
        "--subcategory",
        type=str,
        default=None,
        help="Process only a specific subcategory (e.g. 'gay/incest').",
    )
    parser.add_argument(
        "--limit-stories",
        type=int,
        default=1,
        help="Max number of multi-chapter stories to process.",
    )
    parser.add_argument("--db-path", type=str, default=DB_PATH, help="Path to SQLite DB.")
    parser.add_argument("--spacy-model", type=str, default="en_core_web_sm", help="spaCy model.")
    parser.add_argument(
        "--sentiment-model",
        type=str,
        default="cardiffnlp/twitter-roberta-base-sentiment-latest",
        help="HF Sentiment Model.",
    )
    parser.add_argument("--gpu", action="store_true", default=True, help="Use GPU.")
    return parser.parse_args()


def find_multi_chapter_stories(stories_dir, subcategory=None):
    search_pattern = "*.txt"
    if subcategory:
        base_path = Path(stories_dir) / subcategory
    else:
        base_path = Path(stories_dir)

    all_files = list(base_path.rglob(search_pattern))

    stories_map = defaultdict(list)
    for filepath in all_files:
        stories_map[str(filepath.parent)].append(filepath)

    multi_stories = {k: v for k, v in stories_map.items() if len(v) > 1}
    print(f"Found {len(multi_stories)} multi-chapter stories in {base_path}.")
    return multi_stories


def load_models(spacy_model_name, sentiment_model_name, use_gpu):
    print(f"Loading models (spaCy: {spacy_model_name}, HF: {sentiment_model_name})...")
    device = 0 if use_gpu else -1


def load_models(spacy_model_name, sentiment_model_name, use_gpu):
    print(f"Loading models (spaCy: {spacy_model_name}, HF: {sentiment_model_name})...")
    device = 0 if use_gpu else -1

    if use_gpu:
        try:
            set_gpu_allocator("pytorch")
            require_gpu(0)
            spacy.require_gpu()
        except Exception as e:
            print(f"Could not enable spaCy GPU: {e}")

    nlp = spacy.load(spacy_model_name)
    nlp.add_pipe("sentencizer")

    sentiment_pipe = pipeline(  # pyrefly: ignore [no-matching-overload]
        "sentiment-analysis",
        model=sentiment_model_name,
        device=device,
        truncation=True,
        max_length=512,
    )
    return nlp, sentiment_pipe

    return nlp, sentiment_pipe


def process_chapter(filepath, chapter_idx, story_id, cursor, nlp, sentiment_pipe):
    text = Path(filepath).read_text(encoding="utf-8")
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return
    try:
        doc = nlp(text)
    except Exception as e:
        print(f"spaCy error on {filepath}: {e}")
        return

    try:
        doc = nlp(text)
    except Exception as e:
        print(f"spaCy error on {filepath}: {e}")
        return
    sentences = list(doc.sents)
    if not sentences:
        return

    sentences = list(doc.sents)
    if not sentences:
        return
    sentence_texts = [sent.text for sent in sentences]

    sentence_texts = [sent.text for sent in sentences]
    try:
        sentiments = sentiment_pipe(sentence_texts, batch_size=32)
    except Exception as e:
        print(f"Sentiment pipeline error on {filepath}: {e}")
        sentiments = []
        for sentence_text in sentence_texts:
            try:
                res = sentiment_pipe(sentence_text[:512])[0]
                sentiments.append(res)
            except Exception:
                sentiments.append({"label": "neutral", "score": 0.0})

    try:
        sentiments = sentiment_pipe(sentence_texts, batch_size=32)
    except Exception as e:
        print(f"Sentiment pipeline error on {filepath}: {e}")
        sentiments = []
        for sentence_text in sentence_texts:
            try:
                res = sentiment_pipe(sentence_text[:512])[0]
                sentiments.append(res)
            except Exception:
                sentiments.append({"label": "neutral", "score": 0.0})
    cursor.execute("SELECT MAX(id) FROM sentences")
    row = cursor.fetchone() or (None,)
    last_id_before = row[0] if row[0] is not None else 0
    sentence_batch = []
    entity_batch = []

    for sent_idx, (sent, sent_result) in enumerate(zip(sentences, sentiments)):
        score = get_sentiment_value(sent_result)
        sentence_batch.append((story_id, filepath.name, chapter_idx, sent_idx, sent.text, score))
        sentence_id = last_id_before + 1 + sent_idx
        for ent in sent.ents:
            if ent.label_ in ALLOWED_LABELS:
                entity_batch.append((sentence_id, ent.text, ent.label_))

    cursor.executemany(
        """
        INSERT INTO sentences (story_id, chapter_filename, chapter_index, sentence_index, text, sentiment_score)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        sentence_batch,
    )

    if entity_batch:
        cursor.executemany(
            """
            INSERT INTO sentence_entities (sentence_id, entity_text, entity_label)
            VALUES (?, ?, ?)
            """,
            entity_batch,
        )


def process_story(story_dir, filepaths, cursor, conn, nlp, sentiment_pipe):
    cursor.execute("SELECT id FROM stories WHERE story_dir = ?", (story_dir,))
    if cursor.fetchone():
        print(f"Skipping already processed story: {story_dir}")
        return False
    print(f"\nProcessing Story: {story_dir} ({len(filepaths)} chapters)")
    filepaths.sort(key=lambda x: extract_chapter_number(x.name))

    parts = Path(story_dir).parts
    subcat = "unknown"
    if "test_stories" in parts:
        idx = parts.index("test_stories")
        if len(parts) > idx + 2:
            subcat = f"{parts[idx + 1]}/{parts[idx + 2]}"

    cursor.execute(
        """
        INSERT INTO stories (story_dir, subcategory) VALUES (?, ?)
    """,
        (story_dir, subcat),
    )
    story_id = cursor.lastrowid

    for chapter_idx, filepath in enumerate(tqdm(filepaths, desc="Chapters")):
        process_chapter(filepath, chapter_idx, story_id, cursor, nlp, sentiment_pipe)
        conn.commit()

    return True


def main():
    args = parse_args()

    multi_stories = find_multi_chapter_stories(args.stories_dir, args.subcategory)

    if not multi_stories:
        print("No multi-chapter stories found. Exiting.")
        return None

    conn = init_db(args.db_path)
    cursor = conn.cursor()

    print(f"\nProcessing Story: {story_dir} ({len(filepaths)} chapters)")

    filepaths.sort(key=lambda x: extract_chapter_number(x.name))

    parts = Path(story_dir).parts
    subcat = "unknown"
    if "test_stories" in parts:
        idx = parts.index("test_stories")
        if len(parts) > idx + 2:
            subcat = f"{parts[idx + 1]}/{parts[idx + 2]}"

    cursor.execute(
        "INSERT INTO stories (story_dir, subcategory) VALUES (?, ?)",
        (story_dir, subcat),
    )
    story_id = cursor.lastrowid

    for chapter_idx, filepath in enumerate(tqdm(filepaths, desc="Chapters")):
        process_chapter(filepath, chapter_idx, story_id, cursor, nlp, sentiment_pipe)
        conn.commit()

    return True


def main():
    args = parse_args()

    multi_stories = find_multi_chapter_stories(args.stories_dir, args.subcategory)

    if not multi_stories:
        print("No multi-chapter stories found. Exiting.")
        return

    conn = init_db(args.db_path)
    cursor = conn.cursor()

    nlp, sentiment_pipe = load_models(args.spacy_model, args.sentiment_model, args.gpu)

    processed_stories = 0

    for story_dir, filepaths in multi_stories.items():
        if args.limit_stories and processed_stories >= args.limit_stories:
            break

        was_processed = process_story(story_dir, filepaths, cursor, conn, nlp, sentiment_pipe)
        if was_processed:
            processed_stories += 1
    conn.close()


if __name__ == "__main__":
    main()
