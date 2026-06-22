import os
import re
import threading
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    orientation TEXT,
    category TEXT,
    story_slug TEXT,
    chapter_num INTEGER,
    title TEXT,
    author_name TEXT,
    author_email TEXT,
    publication_date TEXT,
    url TEXT,
    char_count INTEGER,
    word_count INTEGER,
    content TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE VIRTUAL TABLE IF NOT EXISTS stories_fts USING fts5(
    title,
    author_name,
    content,
    content='stories',
    content_rowid='id'
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



def search_all_partitions(
    query: str,
    *,
    category: "str | None" = None,
    author: "str | None" = None,
    date_from: "str | None" = None,
    date_to: "str | None" = None,
    limit: int = 20,
    db_dir: "str | None" = None,
    db_paths: "list[str] | None" = None,
) -> "list[dict]":
    """FTS search across all year-partition databases via ATTACH."""

    if db_paths is not None:
        db_files = [Path(p) for p in db_paths]
    else:
        partition_dir = db_dir or _db_dir
        if not partition_dir:
            return []

        db_files = sorted(Path(partition_dir).glob("*.db"))
        if not db_files:
            return []

        # Filter out stories.db if it exists, since we only want partitions
        db_files = [p for p in db_files if p.name != "stories.db"]

    conditions = ["stories_fts MATCH ?"]
    params = [query]

    if author:
        conditions.append("s.author_name LIKE ?")
        params.append(f"%{author}%")
    if category:
        conditions.append("s.category = ?")
        params.append(category)
    if date_from:
        conditions.append("s.publication_date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("s.publication_date <= ?")
        params.append(date_to)

    where = " AND ".join(conditions)

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    all_rows = []
    for db_path in db_files:
        conn.execute("ATTACH DATABASE ? AS curr_db", (str(db_path),))
        try:
            curs = conn.cursor()
            table_ref = "curr_db.stories"
            fts_ref = "curr_db.stories_fts"
            sql = f"""
                SELECT s.id, s.path, s.category, s.story_slug, s.chapter_num,
                       s.title, s.author_name, s.publication_date, s.url,
                       s.char_count, s.word_count, s.content,
                       snippet({fts_ref}, 2, '<b>', '</b>', '…', 40) AS snippet
                FROM {table_ref} s
                JOIN {fts_ref} ON s.id = {fts_ref}.rowid
                WHERE {where}
                ORDER BY rank
                LIMIT ?
            """
            rows = curs.execute(sql, params + [limit]).fetchall()
            all_rows.extend([dict(r) for r in rows])
            curs.close()
        except sqlite3.OperationalError:
            # Some partitions may not have the expected FTS objects/schema;
            # skip those partitions and continue searching the rest.
            continue
        finally:
            conn.execute("DETACH DATABASE curr_db")

    conn.close()

    # Sort combined results based on FTS rank (which we don't have access to directly,
    # so we sort by whether they have highlighted snippets, then publication date descending)
    all_rows.sort(
        key=lambda r: (
            1 if r.get("snippet") and "<b>" in str(r.get("snippet")) else 0,
            r.get("publication_date") or "",
        ),
        reverse=True,
    )

    return all_rows[:limit]


def optimize_fts() -> None:
    """Rebuild the FTS index for optimal search performance."""
    with _lock:
        conns_to_optimize = []
        if _is_partitioned and _db_dir:
            for db_file in Path(_db_dir).glob("*.db"):
                try:
                    conn = sqlite3.connect(str(db_file), check_same_thread=False)
                    conns_to_optimize.append(conn)
                except sqlite3.Error:
                    pass
        else:
            conns_to_optimize = list(_connections.values())
            if _conn is not None and not _is_partitioned:
                conns_to_optimize.append(_conn)

        for conn in conns_to_optimize:
            try:
                conn.execute("INSERT INTO stories_fts(stories_fts) VALUES ('optimize')")
                conn.commit()
            except sqlite3.OperationalError:
                pass
            finally:
                if _is_partitioned and _db_dir:
                    conn.close()


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
