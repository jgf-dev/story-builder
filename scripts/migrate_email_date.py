#!/usr/bin/env python3
"""Migrate legacy story databases that still include the email_date column."""

import argparse
import sqlite3
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from storybuilder.downloader.db import INDEXES
from storybuilder.downloader.db import SCHEMA
from storybuilder.downloader.db import migrate_legacy_schema


def _prepare_database_file(db_path: Path) -> bool:
    """Ensure a database file uses the current schema."""

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=-64000")
        migrated = migrate_legacy_schema(conn)
        conn.executescript(SCHEMA)
        conn.executescript(INDEXES)
        conn.commit()
        return migrated
    finally:
        conn.close()


def _iter_db_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(path.glob("*.db"))
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate legacy story SQLite databases that still have email_date.")
    parser.add_argument(
        "path",
        nargs="?",
        default="stories/stories.db",
        help="SQLite database file or directory of .db files",
    )
    args = parser.parse_args()

    target = Path(args.path)
    db_files = _iter_db_files(target)
    if not db_files:
        print(f"No database files found at {target}", file=sys.stderr)
        sys.exit(1)

    migrated = 0
    checked = 0
    for db_file in db_files:
        checked += 1
        if _prepare_database_file(db_file):
            migrated += 1
            print(f"Migrated {db_file}")
        else:
            print(f"Up to date {db_file}")

    print(f"Checked {checked} database file(s); migrated {migrated}.")


if __name__ == "__main__":
    main()
