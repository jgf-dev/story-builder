# SQLModel and Monolithic Database Migration Plan

This plan outlines the refactoring of the StoryBuilder database layer to deprecate SQLite database partitioning by year, consolidate all records into a single monolithic database file, and replace raw SQL query strings with SQLModel expressions.

## User Review Required

> [!IMPORTANT]
> **Partitioning Deprecation**: Moving to a monolithic database simplifies the codebase, improves search rankings, and eliminates `ATTACH DATABASE` complexity. All existing databases will be consolidated into `stories.db`.

> [!NOTE]
> **FTS5 Compilation in SQLModel**: We will use pythonic `select()` statements with native SQLAlchemy functions and operators to cleanly represent SQLite FTS5 `MATCH` queries:
> ```python
> literal_column("stories_fts").op("MATCH")(query)
> func.snippet(literal_column("stories_fts"), ...)
> ```

---

## Proposed Changes

### Database Layer (`storybuilder.downloader`)

#### [MODIFY] [db.py](file:///home/jgf2/git/voice/story-builder/src/storybuilder/downloader/db.py)
* Define the `Story` class inheriting from `SQLModel, table=True`.
* Update `init_db(db_path)` to:
  * Check if the path is a directory. If so, automatically resolve to `db_path/stories.db` for backwards compatibility.
  * Create the `stories` table via SQLModel's `SQLModel.metadata.create_all(engine)`.
  * Create the `stories_fts` virtual table and its triggers using raw SQLite DDL commands on the database engine connection (retaining compatibility with SQLite triggers).
* Refactor connections:
  * Remove `_connections` dict, year routing `get_partition_path`, and helper `_get_write_conn`.
  * Replace with a single SQLModel `engine` and global connection configuration.
* Refactor/Rename query functions:
  * Rename `execute_all_partitions(sql, params)` to `execute_query(sql, params)`. Implement using `session.exec(text(sql), params)`.
  * Rename `search_all_partitions(...)` to `search_stories(...)`. Reimplement using pythonic SQLModel `select(Story)` statements joined with `stories_fts` via `literal_column("stories_fts")`, `op("MATCH")`, and `func.snippet()`.
  * Reimplement `insert_story`, `story_exists`, and `get_story` using standard SQLModel CRUD (`session.add(story)`, `session.exec(select(...))`).
  * Reimplement `optimize_fts` to execute on the single monolithic database engine.

---

### Dashboard Data Integration (`storybuilder.dashboard`)

#### [MODIFY] [data.py](file:///home/jgf2/git/voice/story-builder/src/storybuilder/dashboard/data.py)
* Update database references from `stories/db` directory to the single monolithic database.
* Rename calls:
  * Change `storybuilder_db.execute_all_partitions(...)` to `storybuilder_db.execute_query(...)`.
  * Change `storybuilder_db.search_all_partitions(...)` to `storybuilder_db.search_stories(...)`.
* Simplify `get_story_by_path(story_path, db_year)`:
  * Remove partition file loading by year.
  * Query the monolithic database directly using `select(Story).where(Story.path == story_path)`.
* Simplify filters compilation:
  * Categories and authors can be fetched via single SQL queries against the monolithic database.

---

### DB Scripts (`scripts`)

#### [MODIFY] [story_db.py](file:///home/jgf2/git/voice/story-builder/scripts/story_db.py)
* Update all references to `execute_all_partitions` and `search_all_partitions` to the new `execute_query` and `search_stories` signatures.
* Remove partition checking, attachments, and directory traversal code.

---

### Test Suite (`tests`)

#### [MODIFY] [test_database.py](file:///home/jgf2/git/voice/story-builder/tests/downloader/test_database.py)
* Remove year partitioning test cases (like `TestDatabasePartitioning`) since partitioning is deprecated.
* Update existing tests (`TestInsertStory`, `TestFTSSearch`, `TestParseOutputPath`, etc.) to run on the monolithic SQLModel database.
* Update method calls to use `execute_query` and `search_stories`.

---

## Verification Plan

### Automated Tests
* Run the unit test suite to ensure that all refactored database operations and query capabilities are completely green:
  ```bash
  uv run pytest tests/downloader/test_database.py
  uv run pytest
  ```

### Manual Verification
* Start the Streamlit server and search for stories on the Search Explorer page to verify that:
  1. The page loads without error.
  2. Distinct author and category drop-down filters populate instantly.
  3. FTS5 search queries return highlighted text matches and stories.
