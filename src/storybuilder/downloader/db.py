import concurrent.futures

"""
Database layer for story storage -- shared by the downloader (live insert) and
the batch import script.

Thread-safe: uses WAL mode + a write lock.  Call init_db() once at startup,
then insert_story() from any thread.
"""

import os
import re
import sqlite3
import threading
from pathlib import Path

# -- Schema -------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS stories (
    id              INTEGER PRIMARY KEY,
    path            TEXT UNIQUE NOT NULL,
    orientation     TEXT NOT NULL DEFAULT 'gay',
    category        TEXT NOT NULL,
    story_slug      TEXT NOT NULL,
    chapter_num     INTEGER,
    title           TEXT NOT NULL,
    author_name     TEXT,
    author_email    TEXT,
    publication_date TEXT,
    url             TEXT,
    email_date      TEXT,
    char_count      INTEGER NOT NULL,
    word_count      INTEGER NOT NULL,
    content         TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS stories_fts USING fts5(
    title,
    author_name,
    content,
    content=stories,
    content_rowid=id
);

CREATE TRIGGER IF NOT EXISTS stories_ai AFTER INSERT ON stories BEGIN
    INSERT INTO stories_fts(rowid, title, author_name, content)
    VALUES (new.id, new.title, new.author_name, new.content);
END;

CREATE TRIGGER IF NOT EXISTS stories_ad AFTER DELETE ON stories BEGIN
    INSERT INTO stories_fts(stories_fts, rowid, title, author_name, content)
    VALUES ('delete', old.id, old.title, old.author_name, old.content);
END;

CREATE TRIGGER IF NOT EXISTS stories_au AFTER UPDATE ON stories BEGIN
    INSERT INTO stories_fts(stories_fts, rowid, title, author_name, content)
    VALUES ('delete', old.id, old.title, old.author_name, old.content);
    INSERT INTO stories_fts(rowid, title, author_name, content)
    VALUES (new.id, new.title, new.author_name, new.content);
END;
"""

INDEXES = """
CREATE INDEX IF NOT EXISTS idx_stories_category       ON stories(category);
CREATE INDEX IF NOT EXISTS idx_stories_story_slug      ON stories(story_slug);
CREATE INDEX IF NOT EXISTS idx_stories_author_name     ON stories(author_name);
CREATE INDEX IF NOT EXISTS idx_stories_publication_date ON stories(publication_date);
CREATE INDEX IF NOT EXISTS idx_stories_char_count      ON stories(char_count);
"""

# -- Globals ------------------------------------------------------------

_conn: "sqlite3.Connection | None" = None
_connections: dict[str, sqlite3.Connection] = {}
_is_partitioned = False
_db_dir: "str | None" = None
_lock = threading.Lock()

# -- Regex patterns -----------------------------------------------------

_EMAIL_AUTHOR_RE = re.compile(r"^(.+?)\s*<([^>]+)>\s*$")
_CHAPTER_SUFFIX_RE = re.compile(r"^(.+?)-(\d+)\.(txt|html)$")


# -- Author parsing -----------------------------------------------------


def _parse_author(raw: "str | None") -> "tuple[str | None, str | None]":
    """Parse 'Name <email>' or bare email into (name, email)."""
    if not raw:
        return None, None
    raw = raw.strip()
    m = _EMAIL_AUTHOR_RE.match(raw)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    if "@" in raw and "<" not in raw:
        return None, raw.strip()
    return raw.strip(), None


# -- Path parsing -------------------------------------------------------


def _parse_output_path(output_path: str) -> "tuple[str, str, str, int | None]":
    """Extract (orientation, category, story_slug, chapter_num) from a path.

    Path structure (4 parts):  <output_dir>/<orientation>/<category>/<file>
    Path structure (5+ parts): <output_dir>/<orientation>/<category>/<story_slug>/<file>
    """
    parts = Path(output_path).parts
    orientation = "gay"
    category = ""
    story_slug = ""
    chapter_num = None

    filename = parts[-1]

    if len(parts) >= 3:
        orientation = parts[1]
    if len(parts) >= 3:
        category = parts[2]
    if len(parts) >= 5:
        story_slug = parts[3]
    else:
        story_slug = Path(filename).stem

    m = _CHAPTER_SUFFIX_RE.match(filename)
    if m:
        chapter_num = int(m.group(2))
    elif len(parts) >= 5:
        base = Path(filename).stem
        m2 = re.match(r"^.+?-(\d+)$", base)
        if m2:
            chapter_num = int(m2.group(1))

    return orientation, category, story_slug, chapter_num


# -- DB init ------------------------------------------------------------


def init_db(db_path: str) -> "sqlite3.Connection":
    """Initialize the database (idempotent). Returns the connection."""
    global _conn, _is_partitioned, _db_dir

    is_dir = os.path.isdir(db_path) or (
        not db_path.endswith(".db") and not Path(db_path).suffix
    )

    if is_dir:
        os.makedirs(db_path, exist_ok=True)
        _is_partitioned = True
        _db_dir = db_path
        # Return a dummy connection to satisfy get_conn() is not None
        _conn = sqlite3.connect(":memory:", check_same_thread=False)
        return _conn
    else:
        _is_partitioned = False
        _db_dir = None
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        _conn = sqlite3.connect(db_path, check_same_thread=False)
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA synchronous=NORMAL")
        _conn.execute("PRAGMA cache_size=-64000")
        _conn.executescript(SCHEMA)
        _conn.executescript(INDEXES)
        return _conn


def get_conn() -> "sqlite3.Connection | None":
    return _conn


# -- Partition Routing --------------------------------------------------


def get_partition_path(story_date) -> str:
    """Resolve the partitioned database path based on the story's date."""
    if not _db_dir:
        return ""

    year = None
    if not story_date:
        filename = "unknown.db"
    elif hasattr(story_date, "year"):
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

    return os.path.join(_db_dir, filename)


def _get_write_conn(story_date) -> "sqlite3.Connection | None":
    """Get the write connection for the partitioned db or the monolithic db."""
    global _conn
    if not _is_partitioned:
        return _conn

    partition_path = get_partition_path(story_date)
    with _lock:
        if partition_path not in _connections:
            conn = sqlite3.connect(partition_path, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=-64000")
            conn.executescript(SCHEMA)
            conn.executescript(INDEXES)
            _connections[partition_path] = conn
        return _connections[partition_path]


# -- Insert -------------------------------------------------------------


def insert_story(
    *,
    output_path: str,
    title: str,
    author: str,
    story_date: str,
    url: str,
    content: str,
) -> bool:
    """Insert a story into the database. Thread-safe."""
    conn = _get_write_conn(story_date)
    if conn is None:
        return False

    orientation, category, story_slug, chapter_num = _parse_output_path(output_path)
    author_name, author_email = _parse_author(author)
    char_count = len(content)
    word_count = len(content.split())

    sql = """
        INSERT OR REPLACE INTO stories
            (path, orientation, category, story_slug, chapter_num,
             title, author_name, author_email,
             publication_date, url,
             char_count, word_count, content)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        output_path,
        orientation,
        category,
        story_slug,
        chapter_num,
        title,
        author_name,
        author_email,
        story_date,
        url,
        char_count,
        word_count,
        content,
    )

    with _lock:
        try:
            conn.execute(sql, params)
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False


def story_exists(output_path: str, story_date: str) -> bool:
    """Check if a story with the given output path exists in the database."""
    conn = _get_write_conn(story_date)
    if conn is None:
        return False
    with _lock:
        try:
            cursor = conn.execute(
                "SELECT 1 FROM stories WHERE path = ?", (output_path,)
            )
            return cursor.fetchone() is not None
        except Exception:
            return False


def get_story(output_path: str, story_date: str) -> "dict | None":
    """Retrieve a story record from the database."""
    conn = _get_write_conn(story_date)
    if conn is None:
        return None
    with _lock:
        try:
            cursor = conn.execute(
                "SELECT title, author_name, author_email, publication_date, url, content FROM stories WHERE path = ?",
                (output_path,),
            )
            row = cursor.fetchone()
            if row:
                author_name = row[1]
                author_email = row[2]
                if author_name and author_email:
                    author = f"{author_name} <{author_email}>"
                else:
                    author = author_name or author_email or "Unknown"
                return {
                    "title": row[0] or "Unknown",
                    "author": author,
                    "story_date": row[3],
                    "url": row[4],
                    "content": row[5],
                }
            return None
        except Exception:
            return None


def optimize_fts() -> None:
    """Rebuild the FTS index for optimal search performance."""
    with _lock:
        conns = list(_connections.values())
        if _conn is not None and not _is_partitioned:
            conns.append(_conn)

    def _opt(conn: sqlite3.Connection) -> None:
        try:
            conn.execute("INSERT INTO stories_fts(stories_fts) VALUES ('optimize')")
            conn.commit()
        except sqlite3.OperationalError:
            # Best-effort maintenance operation: ignore per-connection optimize
            # failures so search optimization does not interrupt normal writes.
            pass

    if conns:
        # SQLite FTS optimize can be CPU/IO intensive.
        # Using a ThreadPoolExecutor prevents holding the global _lock
        # and blocking other inserts during long optimize operations.
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(len(conns), 10)
        ) as executor:
            list(executor.map(_opt, conns))


def close_db() -> None:
    global _conn, _connections, _is_partitioned, _db_dir
    with _lock:
        if _conn is not None:
            _conn.close()
            _conn = None
        for conn in _connections.values():
            conn.close()
        _connections.clear()
        _is_partitioned = False
        _db_dir = None
