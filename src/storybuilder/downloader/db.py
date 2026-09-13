import bisect
import datetime
import logging as std_logging
import os
import re
import sqlite3
import statistics
import threading
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import ClassVar

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import Table
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy import literal_column
from sqlalchemy.engine import Engine
from sqlmodel import Field
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import col
from sqlmodel import create_engine
from sqlmodel import select
from sqlmodel import text


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
_db_dir: "str | None" = None
_monolithic_db_path: "str | None" = None
_db_path_global: "str | None" = None
_lock = threading.Lock()

# -- Author parsing -----------------------------------------------------

_CHAPTER_SUFFIX_RE = re.compile(r"^(.+?)-(\d+)$")
_KNOWN_ORIENTATIONS = {"gay", "lesbian", "bisexual", "transgender", "bestiality"}

# -- Bulk-touch detection ----------------------------------------------

# Sentinel publication_date for stories whose listing date was destroyed by
# archive-side bulk file rewrites (mtime touch events). Unix epoch keeps them
# identifiable and out of year-over-year distributions.
BULK_TOUCH_EPOCH_DATE = "1970-01-01"

# Organic maximum observed is ~100 stories/day (1993-07-18: 102); bulk-touch
# days run 400-700+. Any exact date above this threshold is an artifact.
BULK_TOUCH_DAY_THRESHOLD = 150


def _parse_author(raw: "str | None") -> "tuple[str | None, str | None]":
	"""Parse 'Name <email>' or bare email into (name, email)."""
	if not raw:
		return None, None
	raw = raw.strip()
	if not raw:
		return None, None

	if raw.endswith(">") and "<" in raw:
		last_lt = raw.rfind("<")
		name_part = raw[:last_lt].strip()
		email_part = raw[last_lt + 1 : -1].strip()
		if email_part:
			return (name_part if name_part else None), email_part

	if "@" in raw and "<" not in raw:
		return None, raw
	return raw, None


# -- Path parsing -------------------------------------------------------


def _parse_output_path(output_path: str) -> "tuple[str, str, str, int | None]":
	"""Extract (orientation, category, story_slug, chapter_num) from a path.

	Path structure (4 parts):  <output_dir>/<orientation>/<category>/<file>
	Path structure (5+ parts): <output_dir>/<orientation>/<category>/<story_slug>/<file>
	"""
	parts = Path(output_path).parts

	if len(parts) < 3:
		raise ValueError(f"Invalid output path: {output_path}. Must have at least 3 parts.")

	# Check if any part matches a known orientation
	orientation_idx = next(
		(i for i, p in enumerate(parts) if p.lower() in _KNOWN_ORIENTATIONS),
		None,
	)

	if orientation_idx is not None and orientation_idx < len(parts) - 1:
		orientation = parts[orientation_idx]
		sub_parts = parts[orientation_idx + 1 :]
		filename_stem = Path(sub_parts[-1]).stem

		if len(sub_parts) == 1:
			category = sub_parts[0]
			story_slug = filename_stem
			chapter_num = None
			if m := _CHAPTER_SUFFIX_RE.match(story_slug):
				story_slug = m.group(1)
				chapter_num = int(m.group(2))
			return orientation, category, story_slug, chapter_num

		if len(sub_parts) == 2:
			category = sub_parts[0]
			story_slug = filename_stem
			chapter_num = None
			if m := _CHAPTER_SUFFIX_RE.match(story_slug):
				story_slug = m.group(1)
				chapter_num = int(m.group(2))
			return orientation, category, story_slug, chapter_num

		# 3+ sub_parts: category, story_slug, ..., file
		category = sub_parts[0]
		story_slug = sub_parts[-2]
		chapter_num = None
		if m := _CHAPTER_SUFFIX_RE.match(story_slug):
			story_slug = m.group(1)
			chapter_num = int(m.group(2))
			return orientation, category, story_slug, chapter_num

		if m := _CHAPTER_SUFFIX_RE.match(filename_stem):
			chapter_num = int(m.group(2))

		return orientation, category, story_slug, chapter_num

	# Fallback legacy behavior
	orientation = parts[1]
	filename_stem = Path(parts[-1]).stem

	if len(parts) == 3:
		category = parts[2]
		story_slug = filename_stem
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

	category = parts[2]
	story_slug = parts[-2]
	chapter_num = None
	if m := _CHAPTER_SUFFIX_RE.match(story_slug):
		story_slug = m.group(1)
		chapter_num = int(m.group(2))
		return orientation, category, story_slug, chapter_num

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
	"""Rebuild legacy story databases that still include the removed email_date column.

	OBSOLETE: The standalone migration script (scripts/migrate_email_date.py) has been
	removed. This now runs only as a defensive self-heal inside init_db / _migrate_schema
	for any remaining legacy database; no new migrations are expected.
	"""
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
	global _conn, _db_dir, _monolithic_db_path, _engine, _db_path_global

	is_dir = Path(db_path).is_dir() or (not db_path.endswith(".db") and not Path(db_path).suffix)

	if is_dir:
		Path(db_path).mkdir(exist_ok=True, parents=True)
		resolved_path = os.path.join(db_path, "stories.db")
	else:
		Path(os.path.dirname(db_path) or ".").mkdir(exist_ok=True, parents=True)
		resolved_path = db_path

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
						Story.publication_date >= date_from,  # pyrefly: ignore [unsupported-operation]
					)
				if date_to:
					query_stmt = query_stmt.where(
						Story.publication_date <= date_to,  # pyrefly: ignore [unsupported-operation]
					)
				if entity_suffixes:
					from sqlalchemy import or_

					or_clauses = [
						col(Story.path).endswith(suffix)
						for suffix in entity_suffixes  # pylint: disable=no-member
					]  # pyrefly: ignore [missing-attribute]  # pylint: disable=no-member
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

				or_clauses = [
					col(Story.path).endswith(suffix)  # pylint: disable=no-member
					for suffix in entity_suffixes  # pylint: disable=no-member
				]  # pyrefly: ignore [missing-attribute]  # pylint: disable=no-member
				stmt = stmt.where(or_(*or_clauses))

			stmt = stmt.order_by(
				col(Story.publication_date).desc(),  # pylint: disable=no-member
			)  # pyrefly: ignore [missing-attribute]  # pylint: disable=no-member
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


def flag_bulk_touched_dates(day_threshold: int = BULK_TOUCH_DAY_THRESHOLD) -> int:
	"""Reset implausibly dense publication dates to the unix-epoch sentinel.

	Archive migrations rewrite file mtimes, so thousands of stories can share
	a listing date unrelated to their real publication date. Any exact date
	carrying more than ``day_threshold`` stories is treated as a bulk-touch
	artifact and every story on it gets
	``publication_date = BULK_TOUCH_EPOCH_DATE``.

	``publication_date`` is not FTS-indexed, so the ``stories_au`` trigger is
	dropped for the duration of the bulk UPDATE (avoiding a full
	re-tokenization of every affected document) and recreated verbatim after.
	Returns the number of rows flagged.
	"""
	conn = _conn
	if conn is None:
		return 0

	with _lock:
		rows = conn.execute(
			"SELECT publication_date FROM stories "
			"WHERE publication_date IS NOT NULL AND publication_date != '' "
			"AND publication_date != ? "
			"GROUP BY publication_date HAVING COUNT(*) > ?",
			(BULK_TOUCH_EPOCH_DATE, day_threshold),
		).fetchall()
		if not rows:
			return 0
		dates = [r[0] for r in rows]

		au = conn.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND name='stories_au'").fetchone()
		try:
			if au:
				conn.execute("DROP TRIGGER stories_au")
			flagged = 0
			chunk_size = 500
			for i in range(0, len(dates), chunk_size):
				chunk = dates[i : i + chunk_size]
				placeholders = ",".join("?" * len(chunk))
				cur = conn.execute(
					f"UPDATE stories SET publication_date=? WHERE publication_date IN ({placeholders})",
					[BULK_TOUCH_EPOCH_DATE, *chunk],
				)
				flagged += cur.rowcount
			conn.commit()
		finally:
			if au:
				conn.execute(au[0])
			conn.commit()

	logging.info(
		"Flagged %d stories on %d bulk-touched dates (>%d/day) as %s: %s%s",
		flagged,
		len(dates),
		day_threshold,
		BULK_TOUCH_EPOCH_DATE,
		", ".join(dates[:5]),
		", ..." if len(dates) > 5 else "",
	)
	return flagged


_DATE_HEADER_RE = re.compile(r"(?m)^Date:\s+(.+)$")


def redate_from_content_headers(
	epoch_date: str = BULK_TOUCH_EPOCH_DATE,
	min_date: str = "1980-01-01",
	dry_run: bool = False,
) -> "dict[str, int]":
	"""Recover true publication dates from embedded usenet ``Date:`` headers.

	Stories flagged by :func:`flag_bulk_touched_dates` still carry their
	original usenet-style ``Date:`` header inside ``content`` in ~80% of
	cases. For each flagged story the first header is parsed (RFC 2822 via
	``email.utils.parsedate_to_datetime``) and, when the resulting date falls
	within ``[min_date, today]``, written back to ``publication_date``.

	``publication_date`` is not FTS-indexed, so the ``stories_au`` trigger is
	dropped for the duration of the batched UPDATE and recreated verbatim
	after. Returns stats: scanned, redated, no_header, parse_failed,
	out_of_range.
	"""
	conn = _conn
	stats = {"scanned": 0, "redated": 0, "no_header": 0, "parse_failed": 0, "out_of_range": 0}
	if conn is None:
		return stats

	min_d = datetime.date.fromisoformat(min_date)
	max_d = datetime.date.today()
	updates: "list[tuple[str, int]]" = []

	with _lock:
		cursor = conn.execute(
			"SELECT id, substr(content, 1, 2000) FROM stories WHERE publication_date = ?",
			(epoch_date,),
		)
		for row_id, head in cursor:
			stats["scanned"] += 1
			if stats["scanned"] % 25000 == 0:
				logging.info("redate scan: %d scanned, %d redatable so far", stats["scanned"], len(updates))
			m = _DATE_HEADER_RE.search(head or "")
			if not m:
				stats["no_header"] += 1
				continue
			try:
				dt = parsedate_to_datetime(m.group(1).strip())
			except (TypeError, ValueError):
				stats["parse_failed"] += 1
				continue
			d = dt.date()
			if d < min_d or d > max_d:
				stats["out_of_range"] += 1
				continue
			updates.append((d.isoformat(), row_id))
		cursor.close()

		stats["redated"] = len(updates)
		if dry_run or not updates:
			logging.info(
				"Redate%s: scanned=%d redatable=%d no_header=%d parse_failed=%d out_of_range=%d",
				" dry run" if dry_run else "",
				stats["scanned"],
				stats["redated"],
				stats["no_header"],
				stats["parse_failed"],
				stats["out_of_range"],
			)
			return stats

		au = conn.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND name='stories_au'").fetchone()
		try:
			if au:
				conn.execute("DROP TRIGGER stories_au")
			conn.executemany("UPDATE stories SET publication_date=? WHERE id=?", updates)
			conn.commit()
		finally:
			if au:
				conn.execute(au[0])
			conn.commit()

	logging.info(
		"Redated %d/%d stories from content Date: headers (no_header=%d, parse_failed=%d, out_of_range=%d)",
		stats["redated"],
		stats["scanned"],
		stats["no_header"],
		stats["parse_failed"],
		stats["out_of_range"],
	)
	return stats


def interpolate_sibling_dates(min_date: str = "1980-01-01", dry_run: bool = False) -> "dict[str, int]":
	"""Estimate dates for epoch-flagged chapters from dated sibling chapters.

	Chapters of a multi-chapter story (same ``category`` + ``story_slug``)
	were posted in chapter order, so dated chapters form a monotonic
	timeline. Epoch-flagged chapters with a ``chapter_num`` get a date by
	linear interpolation between the nearest dated chapters on either side,
	or pace-based extrapolation at the series ends (median days/chapter over
	the 10 most recent known gaps), clamped to ``[min_date, today]``.

	Date-only updates: the ``stories_au`` trigger is bypassed and restored as
	in :func:`redate_from_content_headers`. Returns stats: groups,
	interpolated, extrapolated, skipped_no_chapter, updated.
	"""
	conn = _conn
	stats = {"groups": 0, "interpolated": 0, "extrapolated": 0, "skipped_no_chapter": 0, "updated": 0}
	if conn is None:
		return stats

	min_d = datetime.date.fromisoformat(min_date)
	max_d = datetime.date.today()

	groups = conn.execute(
		"SELECT category, story_slug FROM stories "
		"WHERE story_slug IS NOT NULL "
		"GROUP BY category, story_slug "
		"HAVING SUM(publication_date = ?) > 0 "
		"AND SUM(publication_date != ? AND publication_date >= ?) > 0",
		(BULK_TOUCH_EPOCH_DATE, BULK_TOUCH_EPOCH_DATE, min_date),
	).fetchall()
	stats["groups"] = len(groups)

	updates: "list[tuple[str, int]]" = []
	for category, slug in groups:
		rows = conn.execute(
			"SELECT id, chapter_num, publication_date FROM stories "
			"WHERE category=? AND story_slug=? AND chapter_num IS NOT NULL",
			(category, slug),
		).fetchall()
		known: "dict[int, datetime.date]" = {}
		unknown: "list[tuple[int, int]]" = []
		for rid, ch, pub in rows:
			if pub and pub != BULK_TOUCH_EPOCH_DATE and pub >= min_date:
				try:
					known[ch] = datetime.date.fromisoformat(pub[:10])
				except ValueError:
					continue
			elif pub == BULK_TOUCH_EPOCH_DATE:
				unknown.append((rid, ch))
		stats["skipped_no_chapter"] += conn.execute(
			"SELECT COUNT(*) FROM stories "
			"WHERE category=? AND story_slug=? AND chapter_num IS NULL AND publication_date=?",
			(category, slug, BULK_TOUCH_EPOCH_DATE),
		).fetchone()[0]
		if not known or not unknown:
			continue

		sorted_known = sorted(known.items())
		known_chs = [c for c, _ in sorted_known]
		known_dates = [d for _, d in sorted_known]

		# Median days-per-chapter over the most recent known gaps.
		gaps = [
			((d2 - d1).days / (c2 - c1), c1) for (c1, d1), (c2, d2) in zip(sorted_known, sorted_known[1:]) if c2 > c1
		]
		recent = [g for g, _ in sorted(gaps, key=lambda x: x[1], reverse=True)[:10]]
		pace = max(statistics.median(recent), 0.0) if recent else 30.0

		for rid, ch in unknown:
			idx = bisect.bisect_left(known_chs, ch)
			prev = (known_chs[idx - 1], known_dates[idx - 1]) if idx > 0 else None
			nxt = (known_chs[idx], known_dates[idx]) if idx < len(known_chs) else None
			if prev and nxt:
				span = nxt[0] - prev[0]
				frac = (ch - prev[0]) / span if span else 0.0
				d = prev[1] + datetime.timedelta(days=round((nxt[1] - prev[1]).days * frac))
				stats["interpolated"] += 1
			elif prev:
				d = prev[1] + datetime.timedelta(days=round(pace * (ch - prev[0])))
				stats["extrapolated"] += 1
			elif nxt:
				d = nxt[1] - datetime.timedelta(days=round(pace * (nxt[0] - ch)))
				stats["extrapolated"] += 1
			else:
				continue
			d = max(min_d, min(d, max_d))
			updates.append((d.isoformat(), rid))

	stats["updated"] = len(updates)
	if dry_run or not updates:
		logging.info("Interpolate%s: %s", " dry run" if dry_run else "", stats)
		return stats

	with _lock:
		au = conn.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND name='stories_au'").fetchone()
		try:
			if au:
				conn.execute("DROP TRIGGER stories_au")
			conn.executemany("UPDATE stories SET publication_date=? WHERE id=?", updates)
			conn.commit()
		finally:
			if au:
				conn.execute(au[0])
			conn.commit()

	logging.info("Interpolated dates for %d stories across %d series: %s", len(updates), len(groups), stats)
	return stats


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
	global _conn, _engine, _db_dir, _monolithic_db_path, _db_path_global
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
		_db_dir = None
		_monolithic_db_path = None
		_db_path_global = None
