#!/usr/bin/env python3
"""Split stories/db/2025plus.db into stories/db/2025.db and stories/db/2026plus.db."""

import os
import sys
import sqlite3
import time
from pathlib import Path

# Set up paths to import from src
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from storybuilder.downloader.db import SCHEMA, INDEXES

SRC_DB = "stories/db/2025plus.db"
DST_2025 = "stories/db/2025.db"
DST_2026PLUS = "stories/db/2026plus.db"

COLS = "path, orientation, category, story_slug, chapter_num, title, author_name, author_email, publication_date, url, email_date, char_count, word_count, content"

def init_target_db(path):
    print(f"Initializing {path}...")
    if os.path.exists(path):
        os.remove(path)
    
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.executescript(INDEXES)
    conn.execute("PRAGMA journal_mode=OFF")
    conn.execute("PRAGMA synchronous=OFF")
    conn.commit()
    return conn

def split_partition():
    if not os.path.exists(SRC_DB):
        print(f"Error: Source database {SRC_DB} does not exist.")
        sys.exit(1)

    t0 = time.time()
    
    # Connect to source to get total row count
    src_conn = sqlite3.connect(SRC_DB)
    total_src = src_conn.execute("SELECT COUNT(*) FROM stories").fetchone()[0]
    print(f"Source database contains {total_src:,} stories.")
    src_conn.close()

    # 1. Populate 2025.db
    conn_2025 = init_target_db(DST_2025)
    print("Copying 2025 stories...")
    conn_2025.execute(f"ATTACH ? AS src", (os.path.abspath(SRC_DB),))
    conn_2025.execute(f"""
        INSERT OR IGNORE INTO stories ({COLS})
        SELECT {COLS} FROM src.stories
        WHERE publication_date >= '2025-01-01' AND publication_date < '2026-01-01'
    """)
    conn_2025.commit()
    conn_2025.execute("DETACH src")
    conn_2025.commit()
    
    print("Building FTS5 index for 2025.db...")
    conn_2025.execute("INSERT INTO stories_fts(stories_fts) VALUES ('rebuild')")
    conn_2025.execute("INSERT INTO stories_fts(stories_fts) VALUES ('optimize')")
    conn_2025.commit()
    
    cnt_2025 = conn_2025.execute("SELECT COUNT(*) FROM stories").fetchone()[0]
    print(f"2025.db populated with {cnt_2025:,} stories.")
    conn_2025.close()

    # 2. Populate 2026plus.db
    conn_2026 = init_target_db(DST_2026PLUS)
    print("Copying 2026+ stories...")
    conn_2026.execute(f"ATTACH ? AS src", (os.path.abspath(SRC_DB),))
    conn_2026.execute(f"""
        INSERT OR IGNORE INTO stories ({COLS})
        SELECT {COLS} FROM src.stories
        WHERE publication_date >= '2026-01-01' OR publication_date IS NULL OR publication_date = ''
    """)
    conn_2026.commit()
    conn_2026.execute("DETACH src")
    conn_2026.commit()
    
    print("Building FTS5 index for 2026plus.db...")
    conn_2026.execute("INSERT INTO stories_fts(stories_fts) VALUES ('rebuild')")
    conn_2026.execute("INSERT INTO stories_fts(stories_fts) VALUES ('optimize')")
    conn_2026.commit()
    
    cnt_2026 = conn_2026.execute("SELECT COUNT(*) FROM stories").fetchone()[0]
    print(f"2026plus.db populated with {cnt_2026:,} stories.")
    conn_2026.close()

    # Verification
    total_dst = cnt_2025 + cnt_2026
    print(f"\nVerification:")
    print(f"  Source count: {total_src:,}")
    print(f"  Target total: {total_dst:,} (2025: {cnt_2025:,}, 2026+: {cnt_2026:,})")
    
    if total_src == total_dst:
        print("Success! Row counts match exactly.")
        elapsed = time.time() - t0
        print(f"Split completed in {elapsed:.1f}s.")
    else:
        print("Error: Row counts do NOT match! Do not delete the source database.")
        sys.exit(1)

if __name__ == "__main__":
    split_partition()
