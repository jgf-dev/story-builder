"""StoryBuilder Dashboard - Modular Streamlit application for story archive exploration.

This package re-exports a small legacy module-level API (used by the
tests in ``tests/downloader/test_dashboard.py``) on top of the new
modular layout under ``scripts/dashboard/{config,data,pages,ui}``.

The legacy functions delegate to ``storybuilder.downloader.db`` for
partition queries and to plain sqlite3 for favorites/tags. They are
kept here so existing tests and external imports
(``from dashboard import ...``) continue to work.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

# Re-export the configuration constants so tests can patch them
from .config import BASE_DIR as BASE_DIR  # noqa: F401
from .config import DB_DIR as DB_DIR  # noqa: F401
from .config import STORIES_DIR as STORIES_DIR  # noqa: F401


# Legacy paths used by the old monolithic dashboard.py. Tests patch
# ``dashboard.NLP_DB_PATH`` and ``dashboard.META_DB_PATH`` directly, so
# expose them at the package root.
NLP_DB_PATH = str(
    (Path(__file__).resolve().parents[2] / "stories" / "db" / "nlp_analysis.db")
)
META_DB_PATH = str(
    (Path(__file__).resolve().parents[2] / "stories" / "db" / "dashboard_metadata.db")
)


def get_db_files() -> list[Path]:
    """Return all year-partitioned databases (e.g. ``2025.db``), sorted.

    Mirrors the legacy behaviour of the monolithic ``scripts/dashboard.py``:
    only files matching the ``[0-9][0-9][0-9][0-9].db`` pattern under
    ``DB_DIR`` are returned. Falls back to
    ``storybuilder.downloader.db.get_all_partition_paths`` when the
    directory does not yet exist.
    """
    db_dir = Path(DB_DIR)
    if not db_dir.exists():
        try:
            from storybuilder.downloader import db as sb_db

            paths = sb_db.get_all_partition_paths()
            if paths:
                return sorted(Path(p) for p in paths)
        except Exception:
            pass
        return []
    return sorted(db_dir.glob("[0-9][0-9][0-9][0-9].db"))


def _meta_conn() -> sqlite3.Connection:
    """Return a sqlite3 connection to the metadata DB, creating tables on demand."""
    Path(META_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(META_DB_PATH, check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_path TEXT UNIQUE,
            title TEXT,
            author TEXT,
            tags TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    return conn


def add_favorite(
    story_path: str,
    title: str,
    author: str,
    tags: Optional[str],
    notes: Optional[str],
) -> bool:
    """Insert or update a favorite row. Returns True on success."""
    conn = _meta_conn()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO favorites (story_path, title, author, tags, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (story_path, title, author, tags, notes),
        )
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def remove_favorite(story_path: str) -> bool:
    """Delete a favorite row. Returns True when a row was removed."""
    conn = _meta_conn()
    try:
        cur = conn.execute("DELETE FROM favorites WHERE story_path = ?", (story_path,))
        conn.commit()
        return cur.rowcount > 0
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def get_favorites() -> list[dict]:
    """Return all favorites as a list of dicts, newest first."""
    conn = _meta_conn()
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM favorites ORDER BY created_at DESC")
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def query_stories(
    fts_query: Optional[str] = None,
    category: Optional[str] = None,
    author: Optional[str] = None,
    year_range: Optional[tuple[int, int]] = None,
    entity_text: Optional[str] = None,
    entity_label: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    """Search stories across all partitions and return matching rows.

    Mirrors the legacy ``scripts/dashboard.py.query_stories`` signature
    used by the dashboard tests. Delegates the heavy lifting to
    ``storybuilder.downloader.db.search_all_partitions`` and applies
    entity filtering by consulting the NLP database for path suffixes.
    """
    from storybuilder.downloader import db as sb_db

    # Build date range from year_range tuple if provided
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    if year_range:
        start_year, end_year = year_range
        if start_year:
            date_from = f"{start_year}-01-01"
        if end_year:
            date_to = f"{end_year}-12-31"

    rows = sb_db.search_stories(
        fts_query=fts_query or "",
        category=category,
        author=author,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        snippets=True,
    )

    # Entity filtering: query the NLP DB for path suffixes matching
    # entity text + label, then keep only rows whose ``path`` ends
    # with one of those suffixes. This mirrors the legacy
    # ``scripts/dashboard.py`` behaviour.
    if entity_text:
        entity_suffixes: list[str] = []
        try:
            nlp_db = Path(NLP_DB_PATH)
            if nlp_db.exists():
                nlp_conn = sqlite3.connect(str(nlp_db))
                try:
                    cur = nlp_conn.execute(
                        """
                        SELECT filepath FROM stories s
                        JOIN entities e ON s.id = e.story_id
                        WHERE e.text LIKE ? AND e.label = ?
                        """,
                        (f"%{entity_text}%", entity_label or "PERSON"),
                    )
                    for r in cur.fetchall():
                        parts = Path(r[0]).parts
                        if len(parts) >= 3:
                            entity_suffixes.append("/".join(parts[-3:]))
                finally:
                    nlp_conn.close()
        except sqlite3.Error:
            entity_suffixes = []

        if not entity_suffixes:
            return []

        filtered: list[dict] = []
        for r in rows:
            path = r.get("path", "") or ""
            for suffix in entity_suffixes:
                if path.endswith(suffix):
                    filtered.append(r)
                    break
        rows = filtered

    return rows[:limit]


__all__ = [
    "DB_DIR",
    "BASE_DIR",
    "STORIES_DIR",
    "NLP_DB_PATH",
    "META_DB_PATH",
    "get_db_files",
    "add_favorite",
    "remove_favorite",
    "get_favorites",
    "query_stories",
]
