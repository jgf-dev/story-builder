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


def get_db_filename_from_date(story_date) -> str:
    """Determine the partitioned database filename based on the story publication date."""
    if not story_date:
        return "unknown.db"
    if hasattr(story_date, "year"):
        return f"{story_date.year}.db"

    story_date_str = str(story_date).strip()
    if len(story_date_str) >= 4:
        try:
            year = int(story_date_str[:4])
            return f"{year}.db"
        except ValueError:
            pass

    return "unknown.db"


def get_or_create_connection(
    temp_dir: Path, filename: str, new_conns: dict
) -> sqlite3.Connection:
    """Retrieve an existing connection or create and initialize a new database connection."""
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


def process_source_database(src_path: str, temp_dir: Path, new_conns: dict) -> int:
    """Read all stories from a source database and insert them into the appropriate partitioned databases."""
    print(f"Processing source: {Path(src_path).name}...")
    src_conn = sqlite3.connect(src_path)
    src_conn.row_factory = sqlite3.Row

    try:
        cursor = src_conn.execute("SELECT * FROM stories")
    except sqlite3.OperationalError as e:
        print(f"  Skipping {Path(src_path).name}: {e}")
        src_conn.close()
        return 0

    cols = "path, orientation, category, story_slug, chapter_num, title, author_name, author_email, publication_date, url, char_count, word_count, content"
    placeholders = ", ".join(["?"] * 13)
    insert_sql = f"INSERT OR REPLACE INTO stories ({cols}) VALUES ({placeholders})"

    row_count = 0
    for row in cursor:
        filename = get_db_filename_from_date(row["publication_date"])
        dst_conn = get_or_create_connection(temp_dir, filename, new_conns)

        params = (
            row["path"],
            row["orientation"],
            row["category"],
            row["story_slug"],
            row["chapter_num"],
            row["title"],
            row["author_name"],
            row["author_email"],
            row["publication_date"],
            row["url"],
            row["char_count"],
            row["word_count"],
            row["content"],
        )
        dst_conn.execute(insert_sql, params)
        row_count += 1

        if row_count % 10000 == 0:
            print(f"  Processed {row_count:,} stories from current file...")

    print(f"  Completed {Path(src_path).name}: {row_count:,} stories processed.")
    src_conn.close()
    return row_count


def finalize_new_databases(new_conns: dict):
    """Commit writes and build FTS5 indexes for all new databases."""
    print("Finalizing new databases and building FTS5 indexes...")
    for target_path, conn in new_conns.items():
        conn.commit()
        print(f"  Optimizing FTS for {Path(target_path).name}...")
        conn.execute("INSERT INTO stories_fts(stories_fts) VALUES ('rebuild')")
        conn.execute("INSERT INTO stories_fts(stories_fts) VALUES ('optimize')")
        conn.commit()
        conn.close()


def swap_db_directories(db_path: Path, temp_dir: Path):
    """Back up the old database directory and replace it with the new partitioned directory."""
    backup_dir = db_path.parent / "db_backup"
    if backup_dir.exists():
        shutil.rmtree(backup_dir)

    print("Swapping db directories...")
    os.rename(db_path, backup_dir)
    os.rename(temp_dir, db_path)
    print(f"Migration completed successfully! Old databases backed up to {backup_dir}")


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
    total_moved = 0

    for src_path in db_files:
        total_moved += process_source_database(src_path, temp_dir, new_conns)

    finalize_new_databases(new_conns)

    print(f"Successfully repartitioned {total_moved:,} total stories.")

    swap_db_directories(db_path, temp_dir)


if __name__ == "__main__":
    repartition_dbs("stories/db")
