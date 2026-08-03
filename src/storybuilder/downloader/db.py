import logging as std_logging
import os
import re
import sqlite3
import threading
from pathlib import Path
from typing import ClassVar

from sqlalchemy import func, literal_column
from sqlalchemy.engine import Engine
from sqlmodel import Field, Session, SQLModel, create_engine, select, text

logging = std_logging.getLogger(__name__)

# -- Schema -------------------------------------------------------------


class Story(SQLModel, table=True):
	__tablename__: ClassVar[str] = "stories"  # pyrefly: ignore [bad-override]

	id: int | None = Field(default=None, primary_key=True)
	path: str = Field(unique=True, index=True)
	orientation: str = Field(default="gay", sa_column_kwargs={"server_default": text("'gay'")})
	category: str | None = Field(default=None, index=True)
	story_slug: str | None = Field(default=None, index=True)
	chapter_num: int | None = Field(default=None)
	title: str | None = Field(default=None)
	author_name: str | None = Field(default=None, index=True)
	author_email: str | None = Field(default=None)
	publication_date: str | None = Field(default=None, index=True)
	url: str | None = Field(default=None)
	char_count: int = Field(index=True)
	word_count: int = Field()
	content: str = Field()
	created_at: str | None = Field(default=None, sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")})


from sqlalchemy import Column, Integer, MetaData, Table, Text

metadata_fts = MetaData()
stories_fts = Table(
	"stories_fts",
	metadata_fts,
	Column("rowid", Integer, primary_key=True),
	Column("title", Text),
	Column("author_name", Text),
	Column("content", Text),
)


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
_engine: "Engine | None" = None
_connections: dict[str, sqlite3.Connection] = {}
_is_partitioned = False
_db_dir: "str | None" = None
_monolithic_db_path: "str | None" = None
_db_path_global: "str | None" = None
_lock = threading.Lock()

# -- Regex patterns -----------------------------------------------------

_EMAIL_AUTHOR_RE = re.compile(r"^((?:[^<>\n]+|<[^<>\n]+>)+)\s*<([^<>\n]+)>\s*$")
_CHAPTER_SUFFIX_RE = re.compile(r"^(.+?)-(\d+)$")

# -- Author parsing -----------------------------------------------------


def _parse_author(raw: "str | None") -> "tuple[str | None, str | None]":
	"""Parse 'Name <email>' or bare email into (name, email)."""
	if not raw:
		return None, None
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

	# Expected layouts (parts indices):
	# 3-part:   [output_dir, orientation, file] -> category = filename
	# 4-part:   [output_dir, orientation, category, file]
	# 5+ part:  [output_dir, orientation, category, story_slug, file]

	if len(parts) < 3:
		raise ValueError(f"Invalid output path: {output_path}. Must have at least 3 parts.")

	# orientation is the second path element
	orientation = parts[1]

	filename_stem = Path(parts[-1]).stem

	if len(parts) == 3:
		# category is the filename for the short form, slug is stem
		category = parts[2]
		story_slug = filename_stem
		# detect chapter number in filename (e.g., story-3)
		chapter_num = None
		if m := _CHAPTER_SUFFIX_RE.match(story_slug):
			story_slug = m.group(1)
			chapter_num = int(m.group(2))
		return orientation, category, story_slug, chapter_num

	if len(parts) == 4:
		category = parts[2]
		story_slug = filename_stem
		chapter_num = None
		if m := _CHAPTER_SUFFIX_RE.match(story_slug):
			story_slug = m.group(1)
			chapter_num = int(m.group(2))
		return orientation, category, story_slug, chapter_num

	# 5+ parts: story_slug provided as the penultimate element
	category = parts[2]
	story_slug = parts[-2]
	chapter_num = None
	# If story_slug itself encodes chapter (unlikely), prefer that.
	if m := _CHAPTER_SUFFIX_RE.match(story_slug):
		story_slug = m.group(1)
		chapter_num = int(m.group(2))
		return orientation, category, story_slug, chapter_num

	# Otherwise, check filename for chapter suffix but do not override slug.
	if m := _CHAPTER_SUFFIX_RE.match(filename_stem):
		chapter_num = int(m.group(2))

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

	copy_columns = [col for col in STORY_COLUMNS if col in legacy_columns and col != "email_date"]
	cols_sql = ", ".join(copy_columns)

	try:
		conn.execute("BEGIN")
		if copy_columns:
			conn.execute(f"INSERT OR IGNORE INTO stories ({cols_sql}) SELECT {cols_sql} FROM stories_legacy")
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

	copy_columns = [col for col in STORY_COLUMNS if col in legacy_columns and col != "email_date"]
	if not copy_columns:
		return False

	conn.executescript(
		"""
        DROP TRIGGER IF EXISTS stories_ai;
        DROP TRIGGER IF EXISTS stories_ad;
        DROP TRIGGER IF EXISTS stories_au;
        DROP TABLE IF EXISTS stories_fts;
        """,
	)
	conn.execute("ALTER TABLE stories RENAME TO stories_legacy")
	conn.executescript(SCHEMA)

	cols_sql = ", ".join(copy_columns)
	try:
		conn.execute("BEGIN")
		conn.execute(f"INSERT INTO stories ({cols_sql}) SELECT {cols_sql} FROM stories_legacy")
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
	try:
		conn.execute("INSERT INTO stories_fts(stories_fts) VALUES ('rebuild')")
	except sqlite3.OperationalError:
		logging.debug("Skipping FTS rebuild during legacy schema migration", exc_info=True)
	return True


def _migrate_schema(conn: "sqlite3.Connection") -> None:
	"""Apply schema migrations to an existing partition or database file."""
	migrate_legacy_schema(conn)


# -- DB init ------------------------------------------------------------


def init_db(db_path: str) -> "sqlite3.Connection":
	"""Initialize the database (idempotent). Returns the connection."""
	global _conn, _is_partitioned, _db_dir, _monolithic_db_path, _engine, _db_path_global

	is_dir = Path(db_path).is_dir() or (not db_path.endswith(".db") and not Path(db_path).suffix)

	if is_dir:
		Path(db_path).mkdir(exist_ok=True, parents=True)
		resolved_path = os.path.join(db_path, "stories.db")
	else:
		Path(os.path.dirname(db_path) or ".").mkdir(exist_ok=True, parents=True)
		resolved_path = db_path

	_is_partitioned = False
	_db_dir = os.path.dirname(resolved_path)
	_monolithic_db_path = resolved_path
	_db_path_global = resolved_path

	_engine = create_engine(f"sqlite:///{resolved_path}", connect_args={"check_same_thread": False})

	# Initialize tables via SQLModel metadata
	SQLModel.metadata.create_all(_engine)

	# Retrieve raw DBAPI connection for FTS and trigger execution
	conn = _engine.raw_connection().driver_connection
	if conn is None:
		raise RuntimeError("Failed to retrieve driver connection from engine")
	_conn = conn
	# Configure SQLite pragmas. WAL may not be supported on every filesystem
	# (e.g., some network filesystems). Try WAL first and fall back to DELETE
	# if it fails to avoid a hard crash during test runs.
	try:
		conn.execute("PRAGMA journal_mode=WAL")
	except sqlite3.OperationalError:
		logging.warning("WAL journal mode not available, falling back to DELETE", exc_info=True)
		try:
			conn.execute("PRAGMA journal_mode=DELETE")
		except Exception:
			# best-effort; continue and let later operations surface errors
			logging.debug("Failed to set journal_mode=DELETE", exc_info=True)

	conn.execute("PRAGMA synchronous=NORMAL")
	conn.execute("PRAGMA cache_size=-64000")

	# SQLite DDL commands for FTS virtual table & triggers
	try:
		conn.executescript(SCHEMA)
		conn.executescript(INDEXES)
	except sqlite3.OperationalError as e:
		# Log enough context to diagnose disk I/O issues during schema setup
		logging.exception("Failed to execute DB schema script on %s", resolved_path, exc_info=e)
		raise

	_migrate_schema(conn)
	return conn


def get_conn() -> "sqlite3.Connection | None":
	return _conn


def execute_query(sql: str, params: tuple = ()) -> list[dict]:
	"""Execute a SELECT query against the monolithic database.
	Returns a list of dictionaries.
	"""
	engine = _engine
	if not engine:
		return []

	formatted_sql = sql.format(table="stories")
	with Session(engine) as session:
		try:
			result = session.connection().exec_driver_sql(formatted_sql, params)
			if result.returns_rows:
				return [dict(r) for r in result.mappings()]
			return []
		except Exception as e:
			std_logging.exception("Error executing query: %s", formatted_sql, exc_info=e)
			return []
	# end execute_query


def search_stories(
	fts_query: str = "",
	category: "str | None" = None,
	author: "str | None" = None,
	date_from: "str | None" = None,
	date_to: "str | None" = None,
	**kwargs,
) -> list[dict]:
	"""Search the monolithic database using SQLModel and SQLAlchemy expressions."""
	limit: int = kwargs.get("limit", 100)
	snippets: bool = kwargs.get("snippets", True)
	query: str | None = kwargs.get("query", None)
	entity_suffixes: list[str] | None = kwargs.get("entity_suffixes", None)
	if entity_suffixes == []:
		return []

	if query is not None:
		fts_query = query

	engine = _engine
	if not engine:
		return []

	with Session(engine) as session:
		try:
			if fts_query:
				# Compile Join query for FTS virtual table and Story
				fts_table = stories_fts
				snippet_expr = (
					func.snippet(
						literal_column("stories_fts"),
						2,
						"___HIGHLIGHT_START___",
						"___HIGHLIGHT_END___",
						"…",
						40,
					).label("snippet")
					if snippets
					else literal_column("NULL").label("snippet")
				)

				query_stmt = select(  # pyrefly: ignore [no-matching-overload]
					Story.id,
					Story.path,
					Story.category,
					Story.story_slug,
					Story.title,
					Story.author_name,
					Story.publication_date,
					Story.char_count,
					Story.word_count,
					snippet_expr,
				).select_from(Story)

				if category and category != "All":
					query_stmt = query_stmt.where(Story.category == category)
				if author and author != "All":
					query_stmt = query_stmt.where(Story.author_name == author)
				if date_from:
					query_stmt = query_stmt.where(
						Story.publication_date >= date_from,
					)  # pyrefly: ignore [unsupported-operation]
				if date_to:
					query_stmt = query_stmt.where(
						Story.publication_date <= date_to,
					)  # pyrefly: ignore [unsupported-operation]
				if entity_suffixes:
					from sqlalchemy import or_

					or_clauses = [Story.path.like(f"%{suffix}") for suffix in entity_suffixes]  # pylint: disable=no-member  # pyrefly: ignore [missing-attribute]  # pylint: disable=no-member
					query_stmt = query_stmt.where(or_(*or_clauses))

				query_stmt = query_stmt.join(fts_table, Story.id == fts_table.c.rowid)
				query_stmt = query_stmt.where(literal_column("stories_fts").op("MATCH")(fts_query))
				query_stmt = query_stmt.order_by(literal_column("rank"))
				query_stmt = query_stmt.limit(limit)
				results = session.exec(query_stmt).all()
				output = []
				for row in results:
					output.append(
						{
							"id": row[0],
							"path": row[1],
							"category": row[2],
							"story_slug": row[3],
							"title": row[4],
							"author_name": row[5],
							"publication_date": row[6],
							"char_count": row[7],
							"word_count": row[8],
							"snippet": row[9],
						},
					)
				return output
			# Standard filter path
			stmt = select(Story)
			if category and category != "All":
				stmt = stmt.where(Story.category == category)
			if author and author != "All":
				stmt = stmt.where(Story.author_name == author)
			if date_from:
				stmt = stmt.where(Story.publication_date >= date_from)  # pyrefly: ignore [unsupported-operation]
			if date_to:
				stmt = stmt.where(Story.publication_date <= date_to)  # pyrefly: ignore [unsupported-operation]
			if entity_suffixes:
				from sqlalchemy import or_

				or_clauses = [Story.path.like(f"%{suffix}") for suffix in entity_suffixes]  # pylint: disable=no-member  # pyrefly: ignore [missing-attribute]  # pylint: disable=no-member
				stmt = stmt.where(or_(*or_clauses))

			stmt = stmt.order_by(
				Story.publication_date.desc(),  # pylint: disable=no-member
			)  # pyrefly: ignore [missing-attribute]
			stmt = stmt.limit(limit)
			stories = session.exec(stmt).all()
			output = []
			for s in stories:
				d = s.model_dump()
				d["snippet"] = None
				output.append(d)
			return output
		except Exception as e:
			std_logging.exception("Error executing search_stories", exc_info=e)
			return []


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
	engine = _engine
	if not engine:
		return False

	orientation, category, story_slug, chapter_num = _parse_output_path(output_path)
	author_name, author_email = _parse_author(author)
	char_count = len(content)
	word_count = len(content.split())

	with _lock, Session(engine) as session:
		try:
			# Query if story already exists by path to do INSERT OR REPLACE
			db_story = session.exec(select(Story).where(Story.path == output_path)).first()
			if db_story:
				db_story.orientation = orientation
				db_story.category = category
				db_story.story_slug = story_slug
				db_story.chapter_num = chapter_num
				db_story.title = title
				db_story.author_name = author_name
				db_story.author_email = author_email
				db_story.publication_date = story_date
				db_story.url = url
				db_story.char_count = char_count
				db_story.word_count = word_count
				db_story.content = content
				session.add(db_story)
			else:
				db_story = Story(
					path=output_path,
					orientation=orientation,
					category=category,
					story_slug=story_slug,
					chapter_num=chapter_num,
					title=title,
					author_name=author_name,
					author_email=author_email,
					publication_date=story_date,
					url=url,
					char_count=char_count,
					word_count=word_count,
					content=content,
				)
				session.add(db_story)
			session.commit()
			return True
		except Exception as e:
			session.rollback()
			std_logging.exception("Unexpected error inserting story at %s", output_path, exc_info=e)
			return False


def story_exists(output_path: str, story_date: str = "") -> bool:
	"""Check if a story with the given output path exists in the database."""
	engine = _engine
	if not engine:
		return False
	with Session(engine) as session:
		try:
			db_story = session.exec(select(Story.id).where(Story.path == output_path)).first()
			return db_story is not None
		except Exception as e:
			std_logging.exception("Unexpected error checking story existence at %s", output_path, exc_info=e)
			return False


def get_story(output_path: str, story_date: str = "") -> "dict | None":
	"""Retrieve a story record from the database."""
	engine = _engine
	if not engine:
		return None
	with Session(engine) as session:
		try:
			db_story = session.exec(select(Story).where(Story.path == output_path)).first()
			if db_story:
				author_name = db_story.author_name
				author_email = db_story.author_email
				if author_name and author_email:
					author = f"{author_name} <{author_email}>"
				else:
					author = author_name or author_email or "Unknown"
				return {
					"title": db_story.title or "Unknown",
					"author": author,
					"story_date": db_story.publication_date,
					"url": db_story.url,
					"content": db_story.content,
				}
			return None
		except Exception as e:
			std_logging.exception("Unexpected error retrieving story at %s", output_path, exc_info=e)
			return None


def optimize_fts() -> None:
	"""Rebuild the FTS index for optimal search performance."""
	engine = _engine
	if not engine:
		return
	with Session(engine) as session:
		try:
			session.execute(text("INSERT INTO stories_fts(stories_fts) VALUES ('optimize')"))
			session.commit()
		except Exception as e:
			std_logging.exception("FTS optimize skipped", exc_info=e)


def close_db() -> None:
	global _conn, _engine, _is_partitioned, _db_dir, _monolithic_db_path, _db_path_global
	with _lock:
		if _conn is not None:
			try:
				# Ensure any WAL changes are checkpointed so external connections see the latest data
				_conn.execute("PRAGMA wal_checkpoint(FULL)")
			except Exception:
				logging.debug("WAL checkpoint failed (may be using DELETE journal mode)", exc_info=True)
			_conn.close()
			_conn = None
		if _engine is not None:
			try:
				_engine.dispose()
			except Exception:
				logging.debug("Engine dispose failed", exc_info=True)
		_engine = None
		_is_partitioned = False
		_db_dir = None
		_monolithic_db_path = None
		_db_path_global = None


# Backward-compatible alias
search_all_partitions = search_stories


def get_all_partition_paths() -> list[str]:
	"""Return filesystem paths to partitioned story .db files.

	Provides the function referenced by scripts/dashboard/__init__.py
	for legacy compatibility. Returns paths to year-specific DBs
	when using partitioned mode.
	"""
	from pathlib import Path

	candidates: list[Path] = []
	if _db_dir:
		candidates.append(Path(_db_dir))
	candidates.extend(
		[
			Path.cwd() / "stories" / "db",
			Path("stories") / "db",
			Path("stories"),
		],
	)

	for base in candidates:
		if base.exists() and base.is_dir():
			dbs = sorted(
				str(p)
				for p in base.glob("*.db")
				if not p.name.startswith(".") and p.name not in {"stories.db", "meta.db", "nlp_analysis.db"}
			)
			if dbs:
				return dbs
	return []
