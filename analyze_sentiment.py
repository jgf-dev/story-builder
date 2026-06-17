import argparse
import os
import sqlite3
import re
from pathlib import Path
from collections import defaultdict

import spacy
from thinc.api import require_gpu, set_gpu_allocator
from tqdm import tqdm
from transformers import pipeline

DB_PATH = "sentiment_analysis.db"
ALLOWED_LABELS = {"PERSON", "NORP", "GPE", "LOC", "ORG", "FAC", "EVENT", "PRODUCT", "WORK_OF_ART"}


def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_dir TEXT UNIQUE,
            subcategory TEXT
        )
    """)
    cursor.execute("""
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
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sentence_entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sentence_id INTEGER,
            entity_text TEXT,
            entity_label TEXT,
            FOREIGN KEY(sentence_id) REFERENCES sentences(id)
        )
    """)
    # Indices for faster querying
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sentences_story ON sentences(story_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_sentence ON sentence_entities(sentence_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_text ON sentence_entities(entity_text)")
    
    conn.commit()
    return conn


def get_sentiment_value(result):
    label = result['label'].lower()
    score = result['score']
    # Mapping roberta labels (positive, neutral, negative) or sst2 (POSITIVE, NEGATIVE)
    if 'positive' in label:
        return score
    elif 'negative' in label:
        return -score
    else:
        # Neutral or other
        return 0.0


def extract_chapter_number(filename):
    """Attempts to extract a chapter number from a filename like 'story-name-12.txt'."""
    match = re.search(r'-(\d+)\.txt$', filename)
    if match:
        return int(match.group(1))
    
    # Fallback to any numbers found
    match = re.search(r'(\d+)', filename)
    if match:
        return int(match.group(1))
    
    return 0


def main():
    parser = argparse.ArgumentParser(description="Analyze narrative sentiment and entity interactions.")
    parser.add_argument("--stories-dir", type=str, default="test_stories", help="Directory containing stories.")
    parser.add_argument("--subcategory", type=str, default=None, help="Process only a specific subcategory (e.g. 'gay/incest').")
    parser.add_argument("--limit-stories", type=int, default=1, help="Max number of multi-chapter stories to process.")
    parser.add_argument("--db-path", type=str, default=DB_PATH, help="Path to SQLite DB.")
    parser.add_argument("--spacy-model", type=str, default="en_core_web_sm", help="spaCy model.")
    parser.add_argument("--sentiment-model", type=str, default="cardiffnlp/twitter-roberta-base-sentiment-latest", help="HF Sentiment Model.")
    parser.add_argument("--gpu", action="store_true", default=True, help="Use GPU.")
    args = parser.parse_args()

    # Find stories
    search_pattern = "*.txt"
    if args.subcategory:
        base_path = Path(args.stories_dir) / args.subcategory
    else:
        base_path = Path(args.stories_dir)
        
    all_files = list(base_path.rglob(search_pattern))
    
    # Group by directory
    stories_map = defaultdict(list)
    for filepath in all_files:
        stories_map[str(filepath.parent)].append(filepath)
        
    # Filter for multi-chapter stories
    multi_stories = {k: v for k, v in stories_map.items() if len(v) > 1}
    print(f"Found {len(multi_stories)} multi-chapter stories in {base_path}.")
    
    if not multi_stories:
        print("No multi-chapter stories found. Exiting.")
        return

    # Initialize DB
    conn = init_db(args.db_path)
    cursor = conn.cursor()

    # Initialize models
    print(f"Loading models (spaCy: {args.spacy_model}, HF: {args.sentiment_model})...")
    device = 0 if args.gpu else -1
    
    if args.gpu:
        try:
            set_gpu_allocator("pytorch")
            require_gpu(0)
            spacy.require_gpu()
        except Exception as e:
            print(f"Could not enable spaCy GPU: {e}")
            
    nlp = spacy.load(args.spacy_model)
    nlp.add_pipe("sentencizer") # Ensure sentence boundaries
    
    sentiment_pipe = pipeline(
        "sentiment-analysis", 
        model=args.sentiment_model, 
        device=device,
        truncation=True, 
        max_length=512
    )

    processed_stories = 0
    
    for story_dir, filepaths in multi_stories.items():
        if processed_stories >= args.limit_stories:
            break
            
        # Check if processed
        cursor.execute("SELECT id FROM stories WHERE story_dir = ?", (story_dir,))
        if cursor.fetchone():
            print(f"Skipping already processed story: {story_dir}")
            continue
            
        print(f"\nProcessing Story: {story_dir} ({len(filepaths)} chapters)")
        
        # Sort chapters correctly
        filepaths.sort(key=lambda x: extract_chapter_number(x.name))
        
        # Determine subcategory
        parts = Path(story_dir).parts
        subcat = "unknown"
        if "test_stories" in parts:
            idx = parts.index("test_stories")
            if len(parts) > idx + 2:
                subcat = f"{parts[idx+1]}/{parts[idx+2]}"
        
        cursor.execute("INSERT INTO stories (story_dir, subcategory) VALUES (?, ?)", (story_dir, subcat))
        story_id = cursor.lastrowid
        
        for chapter_idx, filepath in enumerate(tqdm(filepaths, desc="Chapters")):
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
                
            # Quick cleanup
            text = re.sub(r'\s+', ' ', text).strip()
            if not text:
                continue
                
            # SpaCy processing
            # For extremely long chapters, we might need to split, but nlp.max_length usually handles it
            try:
                doc = nlp(text)
            except Exception as e:
                print(f"spaCy error on {filepath}: {e}")
                continue
                
            sentences = list(doc.sents)
            if not sentences:
                continue
                
            # Extract raw string texts for sentiment pipeline
            sentence_texts = [sent.text for sent in sentences]
            
            # Batch sentiment analysis
            try:
                sentiments = sentiment_pipe(sentence_texts, batch_size=32)
            except Exception as e:
                print(f"Sentiment pipeline error on {filepath}: {e}")
                # Fallback to safe sequential processing
                sentiments = []
                for s in sentence_texts:
                    try:
                        res = sentiment_pipe(s[:512])[0]
                        sentiments.append(res)
                    except:
                        sentiments.append({'label': 'neutral', 'score': 0.0})
            
            # Insert sentences and entities
            for sent_idx, (sent, sent_result) in enumerate(zip(sentences, sentiments)):
                score = get_sentiment_value(sent_result)
                
                cursor.execute("""
                    INSERT INTO sentences (story_id, chapter_filename, chapter_index, sentence_index, text, sentiment_score)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (story_id, filepath.name, chapter_idx, sent_idx, sent.text, score))
                
                sentence_id = cursor.lastrowid
                
                # Extract entities from this specific sentence
                # We can filter entities by checking if they fall within the sentence span
                # Or simply re-process the sentence (slower). But `sent.ents` works!
                ents = [e for e in sent.ents if e.label_ in ALLOWED_LABELS and e.text.strip()]
                
                if ents:
                    ent_records = [
                        (sentence_id, e.text.strip(), e.label_) for e in ents
                    ]
                    cursor.executemany("""
                        INSERT INTO sentence_entities (sentence_id, entity_text, entity_label)
                        VALUES (?, ?, ?)
                    """, ent_records)
                    
        conn.commit()
        processed_stories += 1
        
    conn.close()
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()
