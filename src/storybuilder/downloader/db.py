"""
Database layer for story storage -- shared by the downloader (live insert) and
the batch import script.

Thread-safe: uses WAL mode + a write lock.  Call init_db() once at startup,
then insert_story() from any thread.
"""

import concurrent.futures
import os
import re
import sqlite3
import threading
from pathlib import Path

# -- Schema -------------------------------------------------------------

STORY_COLUMNS = (
    "id",
    "path",
    "orientation",
    "category",
    "story_slug",
    "chapter_num",
    "title",
    "author_name",
    "author_email",
    "publication_date",
    "url",
    "char_count",
    "word_count",
    "content",
    "created_at",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS stories (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    path            TEXT UNIQUE NOT NULL,
    orientation     TEXT NOT NULL DEFAULT 'gay',
    category        TEXT,
    story_slug      TEXT,
    chapter_num     INTEGER,
    title           TEXT,
    author_name     TEXT,
    author_email    TEXT,
    publication_date TEXT,
    url             TEXT,
    char_count      INTEGER NOT NULL,
    word_count      INTEGER NOT NULL,
    content         TEXT NOT NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
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


# -- Schema migrations --------------------------------------------------


def _table_columns(conn: sqlite3.Connection, table_name: str) -> list[str]:
    """Return the column names of a table, or an empty list if it does not exist."""
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def _resume_interrupted_migration(conn: sqlite3.Connection) -> bool:
    """Recover data from stories_legacy if a prior schema migration was interrupted."""
    legacy_columns = _table_columns(conn, "stories_legacy")
    if not legacy_columns:
        return False

    copy_columns = [
        col for col in STORY_COLUMNS if col in legacy_columns and col != "email_date"
    ]
    cols_sql = ", ".join(copy_columns)

    try:
        conn.execute("BEGIN")
        if copy_columns:
            conn.execute(
                f"INSERT OR IGNORE INTO stories ({cols_sql}) "
                f"SELECT {cols_sql} FROM stories_legacy"
            )
        conn.execute("DROP TABLE stories_legacy")
        try:
            conn.execute("DELETE FROM sqlite_sequence WHERE name = 'stories'")
        except sqlite3.OperationalError:
            pass
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    conn.executescript(INDEXES)
    return True


def migrate_legacy_schema(conn: sqlite3.Connection) -> bool:
    """Rebuild legacy story databases that still include the removed email_date column."""
    if _resume_interrupted_migration(conn):
        return True

    legacy_columns = _table_columns(conn, "stories")
    if not legacy_columns or "email_date" not in legacy_columns:
        return False

    copy_columns = [
        col for col in STORY_COLUMNS if col in legacy_columns and col != "email_date"
    ]
    if not copy_columns:
        return False

    conn.executescript(
        """
        DROP TRIGGER IF EXISTS stories_ai;
        DROP TRIGGER IF EXISTS stories_ad;
        DROP TRIGGER IF EXISTS stories_au;
        DROP TABLE IF EXISTS stories_fts;
        """
    )
    conn.execute("ALTER TABLE stories RENAME TO stories_legacy")
    conn.executescript(SCHEMA)

    cols_sql = ", ".join(copy_columns)
    try:
        conn.execute("BEGIN")
        conn.execute(
            f"INSERT INTO stories ({cols_sql}) SELECT {cols_sql} FROM stories_legacy"
        )
        conn.execute("DROP TABLE stories_legacy")
        try:
            conn.execute("DELETE FROM sqlite_sequence WHERE name = 'stories'")
        except sqlite3.OperationalError:
            pass
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    conn.executescript(INDEXES)
    return True


def _migrate_schema(conn: "sqlite3.Connection") -> None:
    """Apply schema migrations to an existing partition or database file."""
    migrate_legacy_schema(conn)


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
        _migrate_schema(_conn)
        return _conn


def get_conn() -> "sqlite3.Connection | None":
    return _conn


# -- Partition Routing --------------------------------------------------


def get_all_partition_paths() -> list[str]:
    """Return paths of all partition databases.

    Includes year partitions (e.g. ``2023.db``) as well as the ``unknown.db``
    partition used for stories without a valid date (see get_partition_path).
    Non-partition databases that may live in the same directory -- the
    monolithic ``stories.db`` and the dashboard's ``dashboard_metadata.db``
    (favorites/tags) -- are excluded since they lack the ``stories`` table
    and partition queries should only touch partition files.
    """
    if not _db_dir or not _is_partitioned:
        return []
    import glob

    excluded = {"stories.db", "dashboard_metadata.db"}
    db_files = glob.glob(os.path.join(_db_dir, "*.db"))
    return sorted(p for p in db_files if os.path.basename(p) not in excluded)


def execute_all_partitions(sql: str, params: tuple = ()) -> list[dict]:
    """Execute a SELECT query across all database partitions sequentially
    using ATTACH DATABASE to avoid hitting the SQLITE_MAX_ATTACHED limit.

    The SQL must use {table} where the target table name goes.
    Returns a list of dictionaries.
    """
    if not _is_partitioned:
        conn = get_conn()
        if not conn:
            return []
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(sql.format(table="stories"), params)
        return [dict(r) for r in cursor.fetchall()]

    db_paths = get_all_partition_paths()
    if not db_paths:
        return []

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    all_rows = []

    try:
        for db_path in db_paths:
            try:
                conn.execute("ATTACH DATABASE ? AS curr_db", (db_path,))
                curs = conn.cursor()
                formatted_sql = sql.format(table="curr_db.stories")
                curs.execute(formatted_sql, params)
                all_rows.extend([dict(r) for r in curs.fetchall()])
                curs.close()
            except sqlite3.Error as e:
                print(f"Error querying {db_path}: {e}")
            finally:
                try:
                    conn.execute("DETACH DATABASE curr_db")
                except sqlite3.Error as e:
                    # Best-effort cleanup: if detach fails, continue processing other partitions.
                    print(f"Warning: failed to detach database {db_path}: {e}")
    finally:
        conn.close()

    return all_rows


def search_all_partitions(
    fts_query: str = "",
    category: "str | None" = None,
    author: "str | None" = None,
    date_from: "str | None" = None,
    date_to: "str | None" = None,
    limit: int = 100,
    snippets: bool = True,
    db_dir: "str | None" = None,
    db_paths: "list[str] | None" = None,
    query: "str | None" = None,
) -> list[dict]:
    """Search across all partitions using FTS or fallback to standard filtering."""
    if query is not None:
        fts_query = query
    conditions = ["1=1"]
    params = []

    if category and category != "All":
        conditions.append("s.category = ?")
        params.append(category)
    if author and author != "All":
        conditions.append("s.author_name = ?")
        params.append(author)
    if date_from:
        conditions.append("s.publication_date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("s.publication_date <= ?")
        params.append(date_to)

    where_clause = " AND ".join(conditions)
    all_results = []

    if not _is_partitioned:
        db_paths = [None]
    else:
        partition_dir = db_dir or _db_dir
        if not partition_dir:
            return []
        if partition_dir == _db_dir:
            db_paths = get_all_partition_paths()
        else:
            import glob

            excluded = {"stories.db", "dashboard_metadata.db"}
            db_files = glob.glob(os.path.join(partition_dir, "*.db"))
            db_paths = sorted(
                p for p in db_files if os.path.basename(p) not in excluded
            )
        if not db_paths:
            return []

    def _search_single_db(db_path: "str | None") -> list[dict]:
        conn = None
        need_close = False
        results = []
        try:
            if db_path is None:
                conn = get_conn()
            else:
                conn = sqlite3.connect(db_path)
                need_close = True

            if not conn:
                return results

            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query_params = list(params)

            # Build the snippet expression once, reuse for both branches
            snippet_expr = (
                "snippet(stories_fts, 2, '___HIGHLIGHT_START___', '___HIGHLIGHT_END___', '…', 40)"
                if (fts_query and snippets)
                else "NULL"
            )

            if fts_query:
                # FTS query with optional snippets
                sql = f"""
                    SELECT s.id, s.path, s.category, s.story_slug, s.title, s.author_name,
                           s.publication_date, s.char_count, s.word_count,
                           {snippet_expr} AS snippet
                    FROM stories s
                    JOIN stories_fts ON s.id = stories_fts.rowid
                    WHERE {where_clause} AND stories_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """
                query_params.extend([fts_query, limit])
            else:
                # Non-FTS query: standard filtering and sorting by date
                sql = f"""
                    SELECT s.id, s.path, s.category, s.story_slug, s.title, s.author_name,
                           s.publication_date, s.char_count, s.word_count,
                           NULL AS snippet
                    FROM stories s
                    WHERE {where_clause}
                    ORDER BY s.publication_date DESC
                    LIMIT ?
                """
                query_params.append(limit)

            cursor.execute(sql, query_params)
            results = [dict(r) for r in cursor.fetchall()]

        except sqlite3.Error as e:
            print(f"Error querying {db_path or 'monolithic db'}: {e}")
        finally:
            if need_close and conn:
                conn.close()
        return results

    if db_paths:
        if len(db_paths) == 1 and db_paths[0] is None:
             # Monolithic DB: no need for thread pool
             all_results.extend(_search_single_db(None))
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(db_paths), 10)) as executor:
                for res in executor.map(_search_single_db, db_paths):
                    all_results.extend(res)
    # Sort aggregated results
    if fts_query:
        # Sort by date desc (since rank order is lost when combined, or we could sort by a score if we fetched it)
        all_results.sort(key=lambda x: x.get("publication_date") or "", reverse=True)
    else:
        all_results.sort(key=lambda x: x.get("publication_date") or "", reverse=True)

    return all_results[:limit]


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
            _migrate_schema(conn)
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
        except sqlite3.IntegrityError as e:
            conn.rollback()
            print(f"Integrity error inserting story at {output_path}: {e}")
            return False
        except sqlite3.OperationalError as e:
            conn.rollback()
            print(f"Operational error inserting story at {output_path}: {e}")
            return False
        except Exception as e:
            conn.rollback()
            print(f"Unexpected error inserting story at {output_path}: {e}")
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
        except sqlite3.OperationalError as e:
            print(f"Error checking story existence at {output_path}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error checking story existence at {output_path}: {e}")
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
        except sqlite3.OperationalError as e:
            print(f"Error retrieving story at {output_path}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error retrieving story at {output_path}: {e}")
            return None


def optimize_fts() -> None:
    """Rebuild the FTS index for optimal search performance across all databases."""

    db_paths_to_optimize = []
    with _lock:
        if not _is_partitioned and _conn is not None:
            # Monolithic active
            db_paths_to_optimize = [None]  # None indicates to use the active _conn
        elif _is_partitioned and _db_dir:
            # Gather all partitions
            db_paths_to_optimize = get_all_partition_paths()

    def _opt(path: "str | None") -> None:
        conn = None
        need_close = False
        try:
            if path is None:
                # Monolithic
                with _lock:
                    if _conn:
                        _conn.execute(
                            "INSERT INTO stories_fts(stories_fts) VALUES ('optimize')"
                        )
                        _conn.commit()
            else:
                # Partitions
                conn = sqlite3.connect(path)
                need_close = True
                conn.execute("INSERT INTO stories_fts(stories_fts) VALUES ('optimize')")
                conn.commit()
        except sqlite3.OperationalError as e:
            # Best-effort maintenance operation: ignore per-connection optimize
            # failures so search optimization does not interrupt normal writes.
            print(f"FTS optimize skipped due to OperationalError: {e}")
            pass
        finally:
            if need_close and conn:
                conn.close()

    if db_paths_to_optimize:
        # SQLite FTS optimize can be CPU/IO intensive.
        # Using a ThreadPoolExecutor prevents holding the global _lock
        # and blocking other inserts during long optimize operations.
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(len(db_paths_to_optimize), 10)
        ) as executor:
            list(executor.map(_opt, db_paths_to_optimize))


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
