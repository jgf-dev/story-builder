#!/usr/bin/env python3
"""
Import all Nifty story .txt files into a SQLite database with FTS5 full-text search.

Replaces 73K individual .txt files with a single, searchable database file.
Run this from the repo root.

Usage:
    python scripts/import_to_sqlite.py [--db stories/stories.db] [--limit N] [--force]

Schema:
    stories table — metadata + full text content
    stories_fts   — FTS5 external content index (title, author_name, content)
"""

import argparse
import os
import sqlite3
import sys
import time
from pathlib import Path


# Use shared db module
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# ——— Schema ——————————————————————————————————————————————————————————————————

# Import shared database functions
from storybuilder.downloader.db import _parse_author
from storybuilder.downloader.db import _parse_output_path
from storybuilder.downloader.db import init_db as _db_init_db
from storybuilder.downloader.db import optimize_fts


BATCH_SIZE = 1000


def init_db(db_path: str) -> sqlite3.Connection:
    """Initialize database via shared module."""
    return _db_init_db(db_path)


# ——— Header parsing ————————————————————————————————————————————————————————————


def parse_header(filepath: str) -> "dict | None":
    """Parse the ===== metadata header at the top of a story .txt file.

    Returns a dict with keys: title, author_name, author_email,
    publication_date, url, content.
    Returns None if the file cannot be read or has no valid header.
    """
    try:
        text = Path(filepath).read_text(encoding="utf-8")
    except Exception:
        return None

    lines = text.split("\n")
    if len(lines) < 5:
        return None

    # Check for ===== header markers
    if not lines[0].startswith("===="):
        return None

    title = ""
    author_raw = ""
    pub_date = ""
    url = ""
    email_date = ""

    in_header = True
    content_start = 0
    found_second_marker = False

    for i, line in enumerate(lines):
        if i == 0:
            continue  # Skip first marker
        if in_header and line.startswith("===="):
            found_second_marker = True
            in_header = False
            content_start = i + 1
            continue
        if in_header:
            if line.startswith("Title:"):
                title = line[len("Title:") :].strip()
            elif line.startswith("Author:"):
                author_raw = line[len("Author:") :].strip()
            elif line.startswith("Publication Date:"):
                pub_date = line[len("Publication Date:") :].strip()
            elif line.startswith("URL:"):
                url = line[len("URL:") :].strip()
            elif line.startswith("Email-Date:"):
                email_date = line[len("Email-Date:") :].strip()

    if not found_second_marker:
        return None

    content = "\n".join(lines[content_start:]).strip()
    if not content and not title:
        return None

    author_name, author_email = _parse_author(author_raw)

    return {
        "title": title,
        "author_name": author_name,
        "author_email": author_email,
        "publication_date": pub_date,
        "url": url,
        "email_date": email_date,
        "content": content,
    }


def import_files(
    conn: sqlite3.Connection,
    files: list[str],
    force: bool = False,
) -> tuple[int, int]:
    """Import a list of file paths into the database.

    Returns (imported, skipped).
    """
    imported = 0
    skipped = 0
    batch = []

    for i, filepath in enumerate(files):
        if not Path(filepath).is_file():
            skipped += 1
            continue

        rel_path = os.path.relpath(filepath)
        orientation, category, story_slug, chapter_num = _parse_output_path(rel_path)
        parsed = parse_header(filepath)

        if parsed is None:
            skipped += 1
            continue

        content = parsed["content"]
        char_count = len(content)
        word_count = len(content.split())

        batch.append(
            (
                rel_path,
                orientation,
                category,
                story_slug,
                chapter_num,
                parsed["title"],
                parsed["author_name"],
                parsed["author_email"],
                parsed["publication_date"],
                parsed["url"],
                parsed["email_date"],
                char_count,
                word_count,
                content,
            ),
        )

        if len(batch) >= BATCH_SIZE:
            imported += _flush_batch(conn, batch, force)
            batch = []
            elapsed = time.time() - _start_time
            rate = imported / elapsed if elapsed > 0 else 0
            print(
                f"\r  Imported {imported:,}/{len(files)} files ({rate:.0f}/s) — skipped {skipped}",
                end="",
                flush=True,
            )

    if batch:
        imported += _flush_batch(conn, batch, force)

    return imported, skipped


_start_time = 0.0


def _flush_batch(conn: sqlite3.Connection, batch: list, force: bool) -> int:
    try:
        from storybuilder.downloader.db import _is_partitioned
    except ImportError:
        _is_partitioned = False

    if _is_partitioned:
        from storybuilder.downloader.db import _get_write_conn

        conns = {}
        for row in batch:
            story_date = row[8]
            c = _get_write_conn(story_date)
            if c not in conns:
                conns[c] = []
            conns[c].append(row)
        imported = 0
        for c, rows in conns.items():
            sql = """
                INSERT OR REPLACE INTO stories
                    (path, orientation, category, story_slug, chapter_num,
                     title, author_name, author_email,
                     publication_date, url, email_date,
                     char_count, word_count, content)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            try:
                c.executemany(sql, rows)
                c.commit()
                imported += len(rows)
            except sqlite3.IntegrityError:
                c.rollback()
                if force:
                    count = 0
                    for r in rows:
                        try:
                            c.execute(sql, r)
                            c.commit()
                            count += 1
                        except Exception as e:
                            print(
                                f"[WARN] Skipping row during forced import (path={r[0]!r}): {e}",
                                file=sys.stderr,
                            )
                    imported += count
        return imported

    sql = """
        INSERT OR REPLACE INTO stories
            (path, orientation, category, story_slug, chapter_num,
             title, author_name, author_email,
             publication_date, url, email_date,
             char_count, word_count, content)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    try:
        conn.executemany(sql, batch)
        conn.commit()
        return len(batch)
    except sqlite3.IntegrityError:
        conn.rollback()
        # If force, try one-by-one; otherwise skip whole batch
        if force:
            count = 0
            for row in batch:
                try:
                    conn.execute(sql, row)
                    conn.commit()
                    count += 1
                except Exception:
                    pass
            return count
        return 0


# ——— Main ——————————————————————————————————————————————————————————————————————


def main():
    global _start_time

    parser = argparse.ArgumentParser(description="Import Nifty story .txt files into SQLite + FTS5")
    parser.add_argument(
        "--db",
        default="stories/stories.db",
        help="SQLite database path (default: stories/stories.db)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Import only N files (for testing, default: all)",
    )
    parser.add_argument("--force", action="store_true", help="Force insert even on integrity errors")
    args = parser.parse_args()

    # Collect all .txt files from nifty_stories/
    base_dir = Path("nifty_stories")
    if not base_dir.is_dir():
        print(
            "Error: nifty_stories/ directory not found. Run from repo root.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("Collecting files...")
    all_files = sorted(str(p) for p in base_dir.rglob("*.txt"))
    print(f"  Found {len(all_files):,} .txt files")

    if args.limit:
        all_files = all_files[: args.limit]
        print(f"  Limited to {args.limit:,} files for testing")

    # Re-initialize DB
    if Path(args.db).exists() and not args.force:
        Path(args.db).unlink()

    conn = init_db(args.db)

    print(f"Importing into {args.db}...")
    _start_time = time.time()

    imported, skipped = import_files(conn, all_files, force=args.force)

    elapsed = time.time() - _start_time
    rate = imported / elapsed if elapsed > 0 else 0

    # Build FTS index (should already be built via triggers, but optimize)
    print("\n  Optimizing FTS index...")
    try:
        from storybuilder.downloader.db import _is_partitioned
    except ImportError:
        _is_partitioned = False
    if not _is_partitioned:
        conn.execute("INSERT INTO stories_fts(stories_fts) VALUES ('optimize')")
        conn.commit()
    else:
        optimize_fts()

    # Print stats
    row = conn.execute("SELECT COUNT(*), SUM(char_count), SUM(word_count) FROM stories").fetchone()
    conn.close()

    print(f"\nDone! Imported {imported:,} stories ({skipped} skipped) in {elapsed:.1f}s ({rate:.0f}/s)")
    print(f"  Total stories:  {row[0]:,}")
    if row[1]:
        print(f"  Total chars:    {row[1]:,}")
        print(f"  Total words:    {row[2]:,}")
    print(f"  Database:       {Path(args.db).stat().st_size / (1024 * 1024):.1f} MB")


if __name__ == "__main__":
    main()
