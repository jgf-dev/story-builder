import datetime
import sqlite3
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path

import pandas as pd
import streamlit as st

from storybuilder.dashboard.config import BRACKET_LABELS, LONG_YEAR, get_db_dir, get_meta_db_path, get_nlp_db_path
from storybuilder.downloader import db as storybuilder_db

logger = getLogger(__name__)

MIN_ENTITY_PATH_PARTS = 3


def _ensure_db() -> None:
    """Initialize the storybuilder database engine (idempotent)."""
    storybuilder_db.init_db(get_db_dir())


def get_db_files() -> list[Path]:
    """Retrieve all year-partitioned databases, sorted."""
    db_dir = get_db_dir()
    if not Path(db_dir).exists():
        return []

    return sorted(Path(db_dir).glob("[0-9][0-9][0-9][0-9].db"))


_initialized_meta_dbs: set[str] = set()


def get_meta_conn() -> sqlite3.Connection:
    """Establish connection to local dashboard metadata (favorites & tags)."""
    meta_db_path = get_meta_db_path()
    Path(Path(meta_db_path).parent or ".").mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(meta_db_path, check_same_thread=False)

    if meta_db_path not in _initialized_meta_dbs:
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
            """,
        )
        conn.commit()
        _initialized_meta_dbs.add(meta_db_path)

    return conn


@st.cache_resource
def get_nlp_conn() -> sqlite3.Connection | None:
    """Establish cached connection to NLP database."""
    nlp_db_path = get_nlp_db_path()
    if not Path(nlp_db_path).exists():
        return None
    return sqlite3.connect(nlp_db_path, check_same_thread=False)


@st.cache_data
def get_filter_options() -> tuple[list[str], list[str]]:
    """Compile distinct categories and authors across the database for filters."""
    _ensure_db()
    categories = set()
    authors = set()

    # Get unique categories
    cat_results = storybuilder_db.execute_query("SELECT DISTINCT category FROM {table}")
    for r in cat_results:
        if r.get("category"):
            categories.add(r["category"])

    # Get unique authors
    author_results = storybuilder_db.execute_query("SELECT DISTINCT author_name FROM {table}")
    for r in author_results:
        if r.get("author_name"):
            authors.add(r["author_name"])

    return sorted(categories), sorted(authors)


# ── Archive-stats helpers ───────────────────────────────────────────────


def _init_aggregators() -> dict:
    """Return fresh accumulator dicts for a full aggregation pass."""
    return {
        "year_stats": [],
        "category_counts": {},
        "author_counts": {},
        "bracket_counts": dict.fromkeys(BRACKET_LABELS, 0),
    }


def _format_stats_dataframes(ag: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Convert aggregator dicts into the four final DataFrames."""
    df_years = pd.DataFrame(ag["year_stats"])
    df_cats = pd.DataFrame(list(ag["category_counts"].items()), columns=["Category", "Count"]).sort_values(
        "Count",
        ascending=False,
    )
    df_auths = pd.DataFrame(list(ag["author_counts"].items()), columns=["Author", "Count"]).sort_values(
        "Count",
        ascending=False,
    )
    df_words = pd.DataFrame(
        [
            {"Bracket": label, "Stories": ag["bracket_counts"][label]}
            for label in BRACKET_LABELS
            if (ag["bracket_counts"][label] > 0)
        ],
    )
    return df_years, df_cats, df_auths, df_words


def _safe_query(conn: sqlite3.Connection, sql: str, params: tuple | None = None) -> list:
    """Execute a query safely and fetch all rows, returning an empty list on failure."""
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        return cursor.fetchall()
    except Exception:
        logger.exception("Failed to execute database query: %s", sql)
        return []


@st.cache_data
def load_archive_stats() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Pre-aggregate stats from the monolithic database for the visualizations."""
    _ensure_db()
    ag = _init_aggregators()

    conn = storybuilder_db.get_conn()
    if not conn:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # 1. Year stats
    year_rows = _safe_query(
        conn,
        """
        SELECT CAST(substr(publication_date, 1, 4) AS INTEGER) AS year_val, COUNT(*), SUM(word_count)
        FROM stories
        WHERE publication_date IS NOT NULL AND length(publication_date) >= 4
        GROUP BY year_val
        """,
    )

    # 2. Category counts
    cat_rows = _safe_query(conn, "SELECT category, COUNT(*) FROM stories GROUP BY category")

    # 3. Author counts
    auth_rows = _safe_query(conn, "SELECT author_name, COUNT(*) FROM stories GROUP BY author_name")

    # 4. Bracket counts
    bracket_rows = _safe_query(
        conn,
        """
        SELECT
            CASE
                WHEN word_count < 1000 THEN 'Short (<1K)'
                WHEN word_count < 5000 THEN 'Medium-Short (1K-5K)'
                WHEN word_count < 10000 THEN 'Medium (5K-10K)'
                WHEN word_count < 20000 THEN 'Medium-Long (10K-20K)'
                WHEN word_count < 50000 THEN 'Long (20K-50K)'
                ELSE 'Epic (>50K)'
            END AS bracket,
            COUNT(*)
        FROM stories
        WHERE word_count IS NOT NULL
        GROUP BY bracket
        """,
    )

    for yr, cnt, words in year_rows:
        if yr:
            ag["year_stats"].append({"Year": yr, "Stories Count": cnt, "Total Words": words or 0})

    for cat, cnt in cat_rows:
        if cat:
            ag["category_counts"][cat] = cnt

    for auth, cnt in auth_rows:
        if auth:
            ag["author_counts"][auth] = cnt

    for bracket, cnt in bracket_rows:
        if bracket in ag["bracket_counts"]:
            ag["bracket_counts"][bracket] += cnt

    return _format_stats_dataframes(ag)


# ------------------------------------------------------------------------------
# CORE SEARCH & QUERY ENGINE
# ------------------------------------------------------------------------------


@dataclass
class StorySearchQuery:
    """Parameter bundle for query_stories()."""

    fts_query: str = ""
    category: str = "All"
    author: str = "All"
    year_range: tuple[int, int] | None = None
    entity_text: str = ""
    entity_label: str = "PERSON"
    limit: int = 100


def _resolve_entity_suffixes(
    entity_text: str,
    entity_label: str,
) -> list[str] | None:
    """Query NLP database for story-path suffixes matching entity text + label.

    Returns None when no entity filter is requested (no filtering needed).
    Returns an empty list when the NLP database is unavailable.
    """
    if not entity_text:
        return None

    nlp_conn = get_nlp_conn()
    if not nlp_conn:
        return []

    cursor = nlp_conn.cursor()
    cursor.execute(
        """
        SELECT filepath FROM stories s
        JOIN entities e ON s.id = e.story_id
        WHERE e.text LIKE ? AND e.label = ?
        """,
        (f"%{entity_text}%", entity_label),
    )
    suffixes = []
    for r in cursor.fetchall():
        parts = Path(r[0]).parts
        if len(parts) >= MIN_ENTITY_PATH_PARTS:
            suffixes.append("/".join(parts[-MIN_ENTITY_PATH_PARTS:]))
    return suffixes


def _build_date_range(
    year_range: tuple[int, int] | None,
) -> tuple[str | None, str | None]:
    """Convert a (start, end) year range to ISO date strings."""
    if not year_range:
        return None, None
    return f"{year_range[0]}-01-01", f"{year_range[1]}-12-31"


def _extract_db_year(pub_date: str | int | None) -> int:
    """Extract the 4-digit year from a publication_date value."""
    try:
        if pub_date and len(str(pub_date)) >= LONG_YEAR:
            return int(str(pub_date)[:4])
    except (ValueError, TypeError) as exc:
        logger.debug("Failed to extract year from publication_date=%r: %s", pub_date, exc)
    return datetime.datetime.now(datetime.UTC).year


def _filter_by_entity_suffixes(
    results: list[dict],
    entity_suffixes: list[str] | None,
) -> list[dict]:
    """Remove results whose path doesn't match any entity suffix."""
    if entity_suffixes is None:
        return results  # No entity filter active

    filtered = []
    for r in results:
        for suffix in entity_suffixes:
            if r["path"].endswith(suffix):
                filtered.append(r)
                break
    return filtered


def _enrich_with_db_year(results: list[dict]) -> list[dict]:
    """Inject db_year into each result dict based on publication_date."""
    enriched = []
    for r in results:
        r["db_year"] = _extract_db_year(r.get("publication_date"))
        enriched.append(r)
    return enriched


def query_stories(  # noqa: PLR0913
    params: StorySearchQuery | None = None,
    *,
    fts_query: str = "",
    category: str = "All",
    author: str = "All",
    year_range: tuple[int, int] | None = None,
    entity_text: str = "",
    entity_label: str = "PERSON",
    limit: int = 100,
) -> list[dict]:
    """Search the archive with FTS, filters, and entity-based narrowing."""
    _ensure_db()
    if params is None:
        params = StorySearchQuery(
            fts_query=fts_query,
            category=category,
            author=author,
            year_range=year_range,
            entity_text=entity_text,
            entity_label=entity_label,
            limit=limit,
        )
    entity_suffixes = _resolve_entity_suffixes(params.entity_text, params.entity_label)
    date_from, date_to = _build_date_range(params.year_range)

    raw_results = storybuilder_db.search_stories(
        fts_query=params.fts_query,
        category=params.category,
        author=params.author,
        date_from=date_from,
        date_to=date_to,
        limit=params.limit,
        snippets=True,
        entity_suffixes=entity_suffixes,
    )

    results = _enrich_with_db_year(raw_results)
    return results[: params.limit]


def get_story_by_path(story_path: str, _db_year: int | str | None = None) -> dict | None:
    """Retrieve full text and details of a single story from the monolithic database."""
    _ensure_db()
    conn = storybuilder_db.get_conn()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stories WHERE path = ?", (story_path,))
        row = cursor.fetchone()
        description = cursor.description if row else None
    except Exception:
        logger.exception("Failed to retrieve story by path: %s", story_path)
        return None

    if row:
        if isinstance(row, sqlite3.Row) or hasattr(row, "keys"):
            return dict(row)
        if description:
            cols = [col[0] for col in description]
            return dict(zip(cols, row, strict=False))
    return None


# ------------------------------------------------------------------------------
# FAVORITES OPERATIONS
# ------------------------------------------------------------------------------


def add_favorite(story_path: str, title: str, author: str, tags: str | None, notes: str | None) -> bool:
    conn = get_meta_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO favorites (story_path, title, author, tags, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (story_path, title, author, tags, notes),
        )
        conn.commit()
    except sqlite3.Error:
        return False
    else:
        return True
    finally:
        conn.close()


def remove_favorite(story_path: str) -> bool:
    conn = get_meta_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM favorites WHERE story_path = ?", (story_path,))
        conn.commit()
    except sqlite3.Error:
        return False
    else:
        return True
    finally:
        conn.close()


def get_favorites() -> list[dict]:
    conn = get_meta_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM favorites ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_favorites_publication_years(fav_paths: list[str]) -> dict[str, int]:
    """Resolve the publication year for a list of story paths in bulk."""
    _ensure_db()
    conn = storybuilder_db.get_conn()
    if not conn or not fav_paths:
        return {}

    current_year = datetime.datetime.now(datetime.UTC).year
    path_to_year = {}
    try:
        cursor = conn.cursor()
        placeholders = ",".join("?" for _ in fav_paths)
        # S608 is dynamic SQL composition for placeholders. It's safe since placeholders contains only '?'.
        query = f"SELECT path, publication_date FROM stories WHERE path IN ({placeholders})"  # noqa: S608
        cursor.execute(query, fav_paths)
        rows = cursor.fetchall()
    except Exception:
        logger.exception("Could not resolve story paths from database")
        rows = []

    for row in rows:
        pub_date = row[1] if len(row) > 1 else None
        try:
            y = int(str(pub_date)[:LONG_YEAR]) if pub_date and len(str(pub_date)) >= LONG_YEAR else current_year
        except (ValueError, TypeError):
            y = current_year
        path_to_year[row[0]] = y
    return path_to_year
