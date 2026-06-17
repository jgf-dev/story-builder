#!/usr/bin/env python3
"""
Repartition existing SQLite database files in stories/db into clean single-year partitions (e.g., YYYY.db).
Creates the new partition files in stories/db_repartitioned/ and replaces stories/db/ upon success.
"""

import os
import sys
import glob
import sqlite3
import shutil
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from storybuilder.downloader.db import SCHEMA, INDEXES

def repartition_dbs(db_dir: str):
    db_path = Path(db_dir)
    if not db_path.exists() or not db_path.is_dir():
        print(f"Directory {db_dir} does not exist.")
        return

    # Find all source databases
    db_files = sorted(glob.glob(str(db_path / "*.db")))
    if not db_files:
        print(f"No database files found in {db_dir}.")
        return

    print(f"Found {len(db_files)} database files to repartition.")
    
    # Create temp directory for new partitions
    temp_dir = db_path.parent / "db_repartitioned"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Track connections to the new partitioned databases
    new_conns = {}
    
    def get_new_conn(story_date):
        year = None
        if not story_date:
            filename = "unknown.db"
        elif hasattr(story_date, 'year'):
            year = story_date.year
        else:
            story_date_str = str(story_date).strip()
            if len(story_date_str) < 4:
                filename = "unknown.db"
            else:
                try:
                    year = int(story_date_str[:4])
                except ValueError:
                    filename = "unknown.db"
                    
        if year is not None:
            filename = f"{year}.db"
            
        target_path = str(temp_dir / filename)
        if target_path not in new_conns:
            conn = sqlite3.connect(target_path)
            conn.executescript(SCHEMA)
            conn.executescript(INDEXES)
            conn.execute("PRAGMA journal_mode=OFF")
            conn.execute("PRAGMA synchronous=OFF")
            conn.commit()
            new_conns[target_path] = conn
        return new_conns[target_path]

    total_moved = 0
    
    for src_path in db_files:
        print(f"Processing source: {Path(src_path).name}...")
        src_conn = sqlite3.connect(src_path)
        src_conn.row_factory = sqlite3.Row
        
        try:
            cursor = src_conn.execute("SELECT * FROM stories")
        except sqlite3.OperationalError as e:
            print(f"  Skipping {Path(src_path).name}: {e}")
            src_conn.close()
            continue
            
        # Read and insert
        cols = "path, orientation, category, story_slug, chapter_num, title, author_name, author_email, publication_date, url, email_date, char_count, word_count, content"
        placeholders = ", ".join(["?"] * 14)
        
        insert_sql = f"INSERT OR REPLACE INTO stories ({cols}) VALUES ({placeholders})"
        
        row_count = 0
        for row in cursor:
            story_date = row["publication_date"]
            dst_conn = get_new_conn(story_date)
            
            params = (
                row["path"], row["orientation"], row["category"], row["story_slug"], row["chapter_num"],
                row["title"], row["author_name"], row["author_email"], row["publication_date"],
                row["url"], row["email_date"], row["char_count"], row["word_count"], row["content"]
            )
            dst_conn.execute(insert_sql, params)
            row_count += 1
            total_moved += 1
            
            if row_count % 10000 == 0:
                print(f"  Processed {row_count:,} stories from current file...")
                
        print(f"  Completed {Path(src_path).name}: {row_count:,} stories processed.")
        src_conn.close()

    # Commit all writes and optimize FTS
    print("Finalizing new databases and building FTS5 indexes...")
    for target_path, conn in new_conns.items():
        conn.commit()
        print(f"  Optimizing FTS for {Path(target_path).name}...")
        conn.execute("INSERT INTO stories_fts(stories_fts) VALUES ('rebuild')")
        conn.execute("INSERT INTO stories_fts(stories_fts) VALUES ('optimize')")
        conn.commit()
        conn.close()
        
    print(f"Successfully repartitioned {total_moved:,} total stories.")
    
    # Back up the old directory and swap
    backup_dir = db_path.parent / "db_backup"
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
        
    print("Swapping db directories...")
    os.rename(db_path, backup_dir)
    os.rename(temp_dir, db_path)
    print(f"Migration completed successfully! Old databases backed up to {backup_dir}")

if __name__ == "__main__":
    repartition_dbs("stories/db")
