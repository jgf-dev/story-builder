#!/usr/bin/env python3
"""Tests for the database layer: db.py, import_to_sqlite.py, story_db.py."""

import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


# Ensure the src package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
# Also make scripts/ importable (they don't have __init__.py but we can still import
# the modules directly if we add the parent directory)
_scripts_dir = str(Path(__file__).resolve().parents[2] / "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)


class TestParseAuthor(unittest.TestCase):
    """Tests for _parse_author in storybuilder.downloader.db."""

    def test_name_with_email(self) -> None:
        from storybuilder.downloader.db import _parse_author

        name, email = _parse_author("John Doe <john@example.com>")
        self.assertEqual(name, "John Doe")
        self.assertEqual(email, "john@example.com")

    def test_bare_email(self) -> None:
        from storybuilder.downloader.db import _parse_author

        name, email = _parse_author("anon@test.org")
        self.assertIsNone(name)
        self.assertEqual(email, "anon@test.org")

    def test_name_only(self) -> None:
        from storybuilder.downloader.db import _parse_author

        name, email = _parse_author("Jane Austen")
        self.assertEqual(name, "Jane Austen")
        self.assertIsNone(email)

    def test_none_input(self) -> None:
        from storybuilder.downloader.db import _parse_author

        name, email = _parse_author(None)
        self.assertIsNone(name)
        self.assertIsNone(email)

    def test_empty_string(self) -> None:
        from storybuilder.downloader.db import _parse_author

        name, email = _parse_author("")
        self.assertIsNone(name)
        self.assertIsNone(email)

    def test_name_with_angle_brackets_in_name(self) -> None:
        from storybuilder.downloader.db import _parse_author

        name, email = _parse_author("<Special> Author <special@example.com>")
        self.assertEqual(name, "<Special> Author")
        self.assertEqual(email, "special@example.com")


class TestParseOutputPath(unittest.TestCase):
    """Tests for _parse_output_path in storybuilder.downloader.db."""

    def test_multi_chapter_story(self) -> None:
        from storybuilder.downloader.db import _parse_output_path

        orientation, category, slug, num = _parse_output_path(
            "nifty_stories/gay/adult-friends/my-story/my-story-3.txt"
        )
        self.assertEqual(orientation, "gay")
        self.assertEqual(category, "adult-friends")
        self.assertEqual(slug, "my-story")
        self.assertEqual(num, 3)

    def test_single_chapter_flat(self) -> None:
        from storybuilder.downloader.db import _parse_output_path

        orientation, category, slug, num = _parse_output_path(
            "nifty_stories/gay/adult-friends/my-story.txt"
        )
        self.assertEqual(orientation, "gay")
        self.assertEqual(category, "adult-friends")
        self.assertEqual(slug, "my-story")
        self.assertIsNone(num)

    def test_short_path_fallback(self) -> None:
        from storybuilder.downloader.db import _parse_output_path

        # 3-part path: only output_dir/orientation/file — category = parts[2] = filename
        orientation, category, slug, num = _parse_output_path(
            "nifty_stories/gay/story.txt"
        )
        self.assertEqual(orientation, "gay")
        # With 3 parts, category = parts[2] which is the filename 'story.txt'
        self.assertEqual(category, "story.txt")
        self.assertEqual(slug, "story")  # stem of filename
        self.assertIsNone(num)

    def test_orientation_is_category(self) -> None:
        from storybuilder.downloader.db import _parse_output_path

        orientation, category, slug, num = _parse_output_path(
            "nifty_stories/lesbian/college/title/title-1.txt"
        )
        self.assertEqual(orientation, "lesbian")
        self.assertEqual(category, "college")
        self.assertEqual(slug, "title")
        self.assertEqual(num, 1)

    def test_filename_without_chapter(self) -> None:
        from storybuilder.downloader.db import _parse_output_path

        # 5-part path: downloads/gay/adult-friends/multi/my-story.txt
        # parts[3] = 'multi' is the story_slug directory, not the filename
        orientation, category, slug, num = _parse_output_path(
            "downloads/gay/adult-friends/multi/my-story.txt"
        )
        self.assertEqual(orientation, "gay")
        self.assertEqual(category, "adult-friends")
        self.assertEqual(slug, "multi")  # parts[3], the subdirectory
        self.assertIsNone(num)

    def test_html_file(self) -> None:
        from storybuilder.downloader.db import _parse_output_path

        orientation, category, slug, num = _parse_output_path(
            "nifty_stories/gay/college/slug/story-5.html"
        )
        self.assertEqual(orientation, "gay")
        self.assertEqual(category, "college")
        self.assertEqual(slug, "slug")
        self.assertEqual(num, 5)


class TestDatabaseInit(unittest.TestCase):
    """Tests for init_db, schema, and indexes."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")

    def tearDown(self) -> None:
        # Reset the db module's global connection
        from storybuilder.downloader import db

        db.close_db()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_db_creates_tables(self) -> None:
        from storybuilder.downloader.db import close_db
        from storybuilder.downloader.db import init_db

        conn = init_db(self.db_path)
        try:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
            table_names = [r[0] for r in tables]
            self.assertIn("stories", table_names)
            self.assertIn("stories_fts", table_names)
            self.assertIn("stories_fts_data", table_names)
            self.assertIn("stories_fts_idx", table_names)
        finally:
            close_db()

    def test_init_db_creates_indexes(self) -> None:
        from storybuilder.downloader.db import close_db
        from storybuilder.downloader.db import init_db

        conn = init_db(self.db_path)
        try:
            indexes = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
            ).fetchall()
            index_names = [r[0] for r in indexes]
            self.assertIn("idx_stories_category", index_names)
            self.assertIn("idx_stories_story_slug", index_names)
            self.assertIn("idx_stories_author_name", index_names)
            self.assertIn("idx_stories_publication_date", index_names)
        finally:
            close_db()

    def test_init_db_has_orientation_column(self) -> None:
        from storybuilder.downloader.db import close_db
        from storybuilder.downloader.db import init_db

        conn = init_db(self.db_path)
        try:
            cols = conn.execute("PRAGMA table_info(stories)").fetchall()
            col_names = [c[1] for c in cols]
            self.assertIn("orientation", col_names)
            # orientation should have a default of 'gay'
            orient_col = [c for c in cols if c[1] == "orientation"][0]
            self.assertEqual(orient_col[4], "'gay'")  # default value
            self.assertEqual(orient_col[3], 1)  # NOT NULL
        finally:
            close_db()

    def test_init_db_wal_mode(self) -> None:
        from storybuilder.downloader.db import close_db
        from storybuilder.downloader.db import init_db

        conn = init_db(self.db_path)
        try:
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            self.assertEqual(mode.lower(), "wal")
        finally:
            close_db()

    def test_init_db_migrates_email_date_column(self) -> None:
        from storybuilder.downloader.db import close_db
        from storybuilder.downloader.db import init_db

        legacy_conn = sqlite3.connect(self.db_path)
        legacy_conn.execute(
            """
            CREATE TABLE stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                orientation TEXT,
                category TEXT,
                story_slug TEXT,
                chapter_num INTEGER,
                title TEXT,
                author_name TEXT,
                author_email TEXT,
                email_date TEXT,
                publication_date TEXT,
                url TEXT,
                char_count INTEGER,
                word_count INTEGER,
                content TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        legacy_conn.execute(
            """
            CREATE VIRTUAL TABLE stories_fts USING fts5(
                title,
                author_name,
                content,
                content=stories,
                content_rowid=id
            )
            """
        )
        legacy_conn.execute(
            """
            CREATE TRIGGER stories_ai AFTER INSERT ON stories BEGIN
                INSERT INTO stories_fts(rowid, title, author_name, content)
                VALUES (new.id, new.title, new.author_name, new.content);
            END;
            """
        )
        legacy_conn.execute(
            """
            INSERT INTO stories (
                path, orientation, category, story_slug, chapter_num,
                title, author_name, author_email, email_date,
                publication_date, url,
                char_count, word_count, content, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "nifty_stories/gay/test/legacy.txt",
                "gay",
                "test",
                "legacy",
                1,
                "Legacy Story",
                "Legacy Author",
                "legacy@example.com",
                "2024-01-15",  # email_date
                "2024-01-15",  # publication_date
                "https://example.com/legacy",
                123,
                20,
                "Legacy content here.",
                "2024-01-16 12:34:56",
            ),
        )

        legacy_conn.commit()
        legacy_conn.close()

        conn = init_db(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cols = conn.execute("PRAGMA table_info(stories)").fetchall()
            col_names = [c[1] for c in cols]
            self.assertNotIn("email_date", col_names)
            self.assertIn("created_at", col_names)

            row = conn.execute("SELECT * FROM stories").fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["path"], "nifty_stories/gay/test/legacy.txt")
            self.assertEqual(row["title"], "Legacy Story")
            self.assertEqual(row["publication_date"], "2024-01-15")
            self.assertEqual(row["created_at"], "2024-01-16 12:34:56")

            fts_count = conn.execute(
                "SELECT COUNT(*) FROM stories_fts WHERE stories_fts MATCH 'legacy'"
            ).fetchone()[0]
            self.assertEqual(fts_count, 1)
        finally:
            close_db()


class TestInsertStory(unittest.TestCase):
    """Tests for insert_story function."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")

    def tearDown(self) -> None:
        from storybuilder.downloader import db

        db.close_db()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_insert_and_retrieve(self) -> None:
        from storybuilder.downloader.db import close_db
        from storybuilder.downloader.db import init_db
        from storybuilder.downloader.db import insert_story

        conn = init_db(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            success = insert_story(
                output_path="nifty_stories/gay/adult-friends/story-slug/story-slug-1.txt",
                title="Test Story",
                author="Test Author <test@example.com>",
                story_date="2024-01-15",
                url="https://example.com/story",
                content="This is the story content.",
            )
            self.assertTrue(success)

            row = conn.execute("SELECT * FROM stories").fetchone()
            self.assertEqual(
                row["path"],
                "nifty_stories/gay/adult-friends/story-slug/story-slug-1.txt",
            )
            self.assertEqual(row["orientation"], "gay")
            self.assertEqual(row["category"], "adult-friends")
            self.assertEqual(row["story_slug"], "story-slug")
            self.assertEqual(row["chapter_num"], 1)
            self.assertEqual(row["title"], "Test Story")
            self.assertEqual(row["author_name"], "Test Author")
            self.assertEqual(row["author_email"], "test@example.com")
            self.assertEqual(row["publication_date"], "2024-01-15")
            self.assertEqual(row["url"], "https://example.com/story")
            self.assertEqual(row["char_count"], 26)  # "This is the story content."
            self.assertEqual(row["word_count"], 5)
            self.assertEqual(row["content"], "This is the story content.")
        finally:
            close_db()

    def test_insert_no_author(self) -> None:
        from storybuilder.downloader.db import close_db
        from storybuilder.downloader.db import init_db
        from storybuilder.downloader.db import insert_story

        conn = init_db(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            success = insert_story(
                output_path="nifty_stories/gay/college/story.txt",
                title="Anon Story",
                author="",
                story_date="2023-06-01",
                url="",
                content="Anonymous content.",
            )
            self.assertTrue(success)
            row = conn.execute("SELECT * FROM stories").fetchone()
            self.assertIsNone(row["author_name"])
            self.assertIsNone(row["author_email"])
        finally:
            close_db()

    def test_replace_on_duplicate_path(self) -> None:
        from storybuilder.downloader.db import close_db
        from storybuilder.downloader.db import init_db
        from storybuilder.downloader.db import insert_story

        conn = init_db(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            insert_story(
                output_path="nifty_stories/gay/test/story.txt",
                title="First",
                author="Author One",
                story_date="2022-01-01",
                url="http://a.com",
                content="First content.",
            )
            insert_story(
                output_path="nifty_stories/gay/test/story.txt",
                title="Second",
                author="Author Two",
                story_date="2023-01-01",
                url="http://b.com",
                content="Second content.",
            )
            rows = conn.execute("SELECT * FROM stories").fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["title"], "Second")
            self.assertEqual(rows[0]["content"], "Second content.")
        finally:
            close_db()

    def test_char_and_word_count(self) -> None:
        from storybuilder.downloader.db import close_db
        from storybuilder.downloader.db import init_db
        from storybuilder.downloader.db import insert_story

        conn = init_db(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            insert_story(
                output_path="nifty_stories/gay/test/count.txt",
                title="Count Test",
                author="Tester",
                story_date="2024-01-01",
                url="",
                content="one two three four five",
            )
            row = conn.execute("SELECT * FROM stories").fetchone()
            self.assertEqual(row["word_count"], 5)
            self.assertEqual(row["char_count"], 23)  # "one two three four five"
        finally:
            close_db()


class TestFTSSearch(unittest.TestCase):
    """Tests for FTS5 full-text search."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")

    def tearDown(self) -> None:
        from storybuilder.downloader import db

        db.close_db()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_fts_search_finds_content(self) -> None:
        from storybuilder.downloader.db import close_db
        from storybuilder.downloader.db import init_db
        from storybuilder.downloader.db import insert_story

        conn = init_db(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            insert_story(
                output_path="nifty_stories/gay/test/a.txt",
                title="Vampire Love",
                author="Bram Stoker",
                story_date="1897-05-26",
                url="",
                content="The vampire lurked in the darkness of the castle.",
            )
            insert_story(
                output_path="nifty_stories/gay/test/b.txt",
                title="Werewolf Moon",
                author="Lon Chaney",
                story_date="1941-12-12",
                url="",
                content="Under the full moon the werewolf howled.",
            )

            rows = conn.execute(
                "SELECT s.title, snippet(stories_fts, 1, '<b>', '</b>', '...', 30) "
                "FROM stories s JOIN stories_fts ON s.id = stories_fts.rowid "
                "WHERE stories_fts MATCH 'vampire' ORDER BY rank"
            ).fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["title"], "Vampire Love")

            rows = conn.execute(
                "SELECT s.title FROM stories s "
                "JOIN stories_fts ON s.id = stories_fts.rowid "
                "WHERE stories_fts MATCH 'werewolf' ORDER BY rank"
            ).fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["title"], "Werewolf Moon")
        finally:
            close_db()

    def test_fts_update_on_replace(self) -> None:
        from storybuilder.downloader.db import close_db
        from storybuilder.downloader.db import init_db
        from storybuilder.downloader.db import insert_story

        conn = init_db(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            insert_story(
                output_path="nifty_stories/gay/test/a.txt",
                title="Original",
                author="A",
                story_date="2020-01-01",
                url="",
                content="original vampire content",
            )
            insert_story(
                output_path="nifty_stories/gay/test/a.txt",
                title="Updated",
                author="B",
                story_date="2021-01-01",
                url="",
                content="updated werewolf content",
            )

            # Search for 'vampire' should give no results (was replaced)
            rows = conn.execute(
                "SELECT COUNT(*) FROM stories s "
                "JOIN stories_fts ON s.id = stories_fts.rowid "
                "WHERE stories_fts MATCH 'vampire'"
            ).fetchone()[0]
            self.assertEqual(rows, 0)

            # Search for 'werewolf' should find the updated story
            rows = conn.execute(
                "SELECT s.title FROM stories s "
                "JOIN stories_fts ON s.id = stories_fts.rowid "
                "WHERE stories_fts MATCH 'werewolf'"
            ).fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["title"], "Updated")
        finally:
            close_db()

    def test_optimize_fts_all(self) -> None:
        from storybuilder.downloader import db

        # Initialize with monolithic database path
        db.init_db(self.db_path)

        # Insert stories
        db.insert_story(
            output_path="nifty_stories/gay/adult-friends/story1.txt",
            title="2012 Story",
            author="Author One",
            story_date="2012-05-14",
            url="http://example.com/1",
            content="Content for story 1.",
        )
        db.insert_story(
            output_path="nifty_stories/gay/college/story2.txt",
            title="2025 Story",
            author="Author Two",
            story_date="2025-05-10",
            url="http://example.com/2",
            content="Content for story 2.",
        )

        db.optimize_fts()

        # Verify search works after optimize
        results = db.search_stories(fts_query="Content")
        self.assertEqual(len(results), 2)



class TestParseHeader(unittest.TestCase):
    """Tests for parse_header in import_to_sqlite.py."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_story_file(self, fname: str, content: str) -> str:
        path = os.path.join(self.temp_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_standard_header(self) -> None:
        content = (
            "=" * 80 + "\n"
            "Title: My Story\n"
            "Author: Jane Writer <jane@email.com>\n"
            "Publication Date: 2024-06-13\n"
            "URL: https://example.com/story\n"
            + "=" * 80
            + "\n\n"
            + "Once upon a time there was a story.\n"
            "It had multiple paragraphs.\n"
        )
        path = self._write_story_file("test.txt", content)
        import import_to_sqlite

        result = import_to_sqlite.parse_header(path)
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "My Story")
        self.assertEqual(result["author_name"], "Jane Writer")
        self.assertEqual(result["author_email"], "jane@email.com")
        self.assertEqual(result["publication_date"], "2024-06-13")
        self.assertEqual(result["url"], "https://example.com/story")
        self.assertIn("Once upon a time", result["content"])
        self.assertIn("multiple paragraphs", result["content"])

    def test_header_with_email_date(self) -> None:
        content = (
            "=" * 80 + "\n"
            "Title: Email Story\n"
            "Author: user@host.com\n"
            "Publication Date: 2023-01-01\n"
            "URL: https://example.com\n" + "=" * 80 + "\n\n" + "Email content here.\n"
        )
        path = self._write_story_file("email.txt", content)
        import import_to_sqlite

        result = import_to_sqlite.parse_header(path)
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Email Story")
        self.assertIsNone(result["author_name"])
        self.assertEqual(result["author_email"], "user@host.com")

    def test_missing_file(self) -> None:
        import import_to_sqlite

        result = import_to_sqlite.parse_header("/nonexistent/file.txt")
        self.assertIsNone(result)

    def test_no_header_marker(self) -> None:
        content = "Just plain text without any header markers.\n"
        path = self._write_story_file("noheader.txt", content)
        import import_to_sqlite

        result = import_to_sqlite.parse_header(path)
        self.assertIsNone(result)

    def test_minimal_header(self) -> None:
        import import_to_sqlite

        content = (
            "=" * 80 + "\n"
            "Title: Minimal\n"
            "Author: Min\n"
            "Publication Date: 2024-01-01\n"
            "URL: http://x.com\n" + "=" * 80 + "\n\n" + "body"
        )
        path = self._write_story_file("min.txt", content)
        result = import_to_sqlite.parse_header(path)
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Minimal")
        self.assertEqual(result["content"], "body")

    def test_empty_content(self) -> None:
        import import_to_sqlite

        content = (
            "=" * 80 + "\n"
            "Title: Empty\n"
            "Author: Nobody\n"
            "Publication Date: 2024-01-01\n"
            "URL: http://x.com\n" + "=" * 80 + "\n\n"
        )
        path = self._write_story_file("empty.txt", content)
        result = import_to_sqlite.parse_header(path)
        # returns None because content is empty and title is there but content is empty string
        # Actually, empty content + title = not None since we check "not content and not title"
        self.assertIsNotNone(result)
        self.assertEqual(result["content"], "")
<<<<<<< HEAD
=======

    def test_import_to_sqlite_script_compiles(self) -> None:
        script_path = Path(__file__).resolve().parents[2] / "scripts" / "import_to_sqlite.py"
        with tempfile.TemporaryDirectory() as tmp:
            py_compile.compile(
                str(script_path),
                cfile=os.path.join(tmp, "import_to_sqlite.pyc"),
                doraise=True,
            )


>>>>>>> origin/main
class TestMonolithicDatabase(unittest.TestCase):
    """Tests for monolithic SQLModel-based database in db.py."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "stories.db")

    def tearDown(self) -> None:
        from storybuilder.downloader import db
        db.close_db()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_db_creates_schema(self) -> None:
        from storybuilder.downloader import db
        conn = db.init_db(self.db_path)
        self.assertIsNotNone(conn)

        # Verify stories table exists
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stories'")
        self.assertIsNotNone(cursor.fetchone())

        # Verify stories_fts exists
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stories_fts'")
        self.assertIsNotNone(cursor.fetchone())

    def test_insert_and_retrieve_story(self) -> None:
        from storybuilder.downloader import db
        db.init_db(self.db_path)

        success = db.insert_story(
            output_path="nifty_stories/gay/adult-friends/test-story.txt",
            title="My Special Test Story",
            author="Author Name <author@example.com>",
            story_date="2026-07-05",
            url="http://example.com/test",
            content="This is the content of my special test story with unique word banana.",
        )
        self.assertTrue(success)

        # Check story_exists
        self.assertTrue(db.story_exists("nifty_stories/gay/adult-friends/test-story.txt"))

        # Retrieve story
        story = db.get_story("nifty_stories/gay/adult-friends/test-story.txt")
        self.assertIsNotNone(story)
        self.assertEqual(story["title"], "My Special Test Story")
        self.assertEqual(story["author"], "Author Name <author@example.com>")
        self.assertEqual(story["story_date"], "2026-07-05")
        self.assertEqual(story["content"], "This is the content of my special test story with unique word banana.")

    def test_execute_query(self) -> None:
        from storybuilder.downloader import db
        db.init_db(self.db_path)
        db.insert_story(
            output_path="nifty_stories/gay/adult-friends/test-story.txt",
            title="Test Story",
            author="Author",
            story_date="2026-07-05",
            url="http://example.com",
            content="Content",
        )

        rows = db.execute_query("SELECT COUNT(*) as cnt FROM {table}")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["cnt"], 1)

    def test_search_stories_fts(self) -> None:
        from storybuilder.downloader import db
        db.init_db(self.db_path)
        db.insert_story(
            output_path="nifty_stories/gay/adult-friends/test-story.txt",
            title="Banana Story",
            author="Monkey",
            story_date="2026-07-05",
            url="http://example.com",
            content="Monkey loves eating fresh sweet banana fruit everyday.",
        )

        # Full-text search matching banana
        results = db.search_stories(fts_query="banana", snippets=True)
        self.assertEqual(len(results), 1)
        self.assertIn("banana", results[0]["snippet"])



class TestImportToSQLite(unittest.TestCase):
    def _write_story_file(self, filename: str, content: str) -> str:
        path = os.path.join(self.temp_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_header_valid(self) -> None:
        import import_to_sqlite

        content = (
            "================================================================================\n"
            "Title: Test Story\n"
            "Author: John Doe <john@example.com>\n"
            "Publication Date: 2024-01-01\n"
            "URL: http://example.com/story\n"
            "================================================================================\n"
            "\n"
            "This is the body of the story.\n"
            "It has multiple lines.\n"
        )
        path = self._write_story_file("valid.txt", content)
        result = import_to_sqlite.parse_header(path)

        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Test Story")
        self.assertEqual(result["author_name"], "John Doe")
        self.assertEqual(result["author_email"], "john@example.com")
        self.assertEqual(result["publication_date"], "2024-01-01")
        self.assertEqual(result["url"], "http://example.com/story")
        self.assertEqual(
            result["content"], "This is the body of the story.\nIt has multiple lines."
        )

    def test_parse_header_missing_fields(self) -> None:
        import import_to_sqlite

        content = (
            "================================================================================\n"
            "Title: No Author Story\n"
            "Publication Date: 2024-02-01\n"
            "================================================================================\n"
            "\n"
            "Body content here."
        )
        path = self._write_story_file("missing.txt", content)
        result = import_to_sqlite.parse_header(path)
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "No Author Story")
        self.assertIsNone(result["author_name"])
        self.assertIsNone(result["author_email"])
        self.assertEqual(result["publication_date"], "2024-02-01")
        self.assertEqual(result["content"], "Body content here.")

    def test_parse_header_invalid_format(self) -> None:
        import import_to_sqlite

        # Missing the second divider
        content = (
            "================================================================================\n"
            "Title: Bad Format\n"
            "Author: Me\n"
            "Some content that is not a header."
        )
        path = self._write_story_file("invalid.txt", content)
        result = import_to_sqlite.parse_header(path)
        self.assertIsNone(result)

    def test_minimal_header(self) -> None:
        import import_to_sqlite

        content = (
            "=" * 80 + "\n"
            "Title: Minimal\n"
            "Author: Min\n"
            "Publication Date: 2024-01-01\n"
            "URL: http://x.com\n" + "=" * 80 + "\n\n" + "body"
        )
        path = self._write_story_file("min.txt", content)
        result = import_to_sqlite.parse_header(path)
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Minimal")
        self.assertEqual(result["content"], "body")

    def test_empty_content(self) -> None:
        import import_to_sqlite

        content = (
            "=" * 80 + "\n"
            "Title: Empty\n"
            "Author: Nobody\n"
            "Publication Date: 2024-01-01\n"
            "URL: http://x.com\n" + "=" * 80 + "\n\n"
        )
        path = self._write_story_file("empty.txt", content)
        result = import_to_sqlite.parse_header(path)
        self.assertIsNotNone(result)
        self.assertEqual(result["content"], "")

    def test_flush_batch_compatibility(self) -> None:
        import import_to_sqlite

        from storybuilder.downloader import db

        db_path = os.path.join(self.temp_dir, "import_test.db")
        conn = db.init_db(db_path)

        batch = [
            (
                "nifty_stories/gay/category/slug/slug.txt",
                "gay",
                "category",
                "slug",
                None,
                "Title",
                "Author",
                "author@example.com",
                "2024-01-01",
                "http://example.com",
                100,
                20,
                "Content body",
            )
        ]
        inserted = import_to_sqlite._flush_batch(conn, batch, force=False)
        self.assertEqual(inserted, 1)

        cur = conn.execute("SELECT title, author_name, content FROM stories WHERE path = ?", (batch[0][0],))
        row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "Title")
        conn.close()


class TestDBSearch(unittest.TestCase):
    """Tests for search_stories and related functions."""

    def setUp(self) -> None:
        import tempfile

        from storybuilder.downloader import db

        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        db.init_db(self.db_path)

        db.insert_story(
            output_path="/tmp/story1.txt",
            title="Love Story",
            author="Author A",
            story_date="2024-06-01",
            url="http://ex/1",
            content="A story about love and romance",
        )
        db.insert_story(
            output_path="/tmp/story2.txt",
            title="Adventure Tale",
            author="Author B",
            story_date="2024-07-15",
            url="http://ex/2",
            content="An adventure in the mountains",
        )

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_search_stories_basic(self) -> None:
        from storybuilder.downloader import db

        results = db.search_stories("love")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Love Story")

    def test_search_stories_with_category_filter(self) -> None:
        from storybuilder.downloader import db

        results = db.search_stories("adventure", category="gay")
        self.assertIsInstance(results, list)

    def test_search_stories_with_author_filter(self) -> None:
        from storybuilder.downloader import db

        results = db.search_stories("", author="Author A")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["author_name"], "Author A")

    def test_search_stories_date_range(self) -> None:
        from storybuilder.downloader import db

        results = db.search_stories("", date_from="2024-06-01", date_to="2024-06-30")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Love Story")

    def test_search_stories_no_results(self) -> None:
        from storybuilder.downloader import db

        results = db.search_stories("nonexistent_word_xyz")
        self.assertEqual(len(results), 0)

    def test_search_stories_limit(self) -> None:
        from storybuilder.downloader import db

        results = db.search_stories("", limit=1)
        self.assertLessEqual(len(results), 1)


class TestDBParseOutputPath(unittest.TestCase):
    """Tests for _parse_output_path.

    Path format: output_dir/orientation/category/file (relative, no leading /)
    """

    def test_parse_4part_path(self) -> None:
        """4-part: output/orientation/category/file"""
        from storybuilder.downloader.db import _parse_output_path

        orientation, category, story_slug, chapter = _parse_output_path(
            "output/gay/romance/story.txt"
        )
        self.assertEqual(orientation, "gay")
        self.assertEqual(category, "romance")
        self.assertEqual(story_slug, "story")

    def test_parse_5part_path(self) -> None:
        """5-part: output/orientation/category/slug/file"""
        from storybuilder.downloader.db import _parse_output_path

        orientation, category, story_slug, chapter = _parse_output_path(
            "output/gay/series/my-story/ch1.txt"
        )
        self.assertEqual(orientation, "gay")
        self.assertEqual(category, "series")
        self.assertEqual(story_slug, "my-story")

    def test_parse_3part_path(self) -> None:
        """3-part: output/orientation/file"""
        from storybuilder.downloader.db import _parse_output_path

        orientation, category, story_slug, chapter = _parse_output_path(
            "output/gay/some-story.txt"
        )
        self.assertEqual(orientation, "gay")
        self.assertEqual(category, "some-story.txt")  # full filename for 3-part
        self.assertEqual(story_slug, "some-story")

    def test_parse_with_chapter_suffix(self) -> None:
        from storybuilder.downloader.db import _parse_output_path

        orientation, category, story_slug, chapter = _parse_output_path(
            "output/gay/series/chapter-5.txt"
        )
        self.assertEqual(story_slug, "chapter")
        self.assertEqual(chapter, 5)

    def test_parse_invalid_too_short(self) -> None:
        from storybuilder.downloader.db import _parse_output_path

        with self.assertRaises(ValueError):
            _parse_output_path("short.txt")


class TestDBContentOperations(unittest.TestCase):
    """Tests for content update/delete operations."""

    def setUp(self) -> None:
        import tempfile

        from storybuilder.downloader import db

        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        db.init_db(self.db_path)

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_get_story_returns_all_fields(self) -> None:
        from storybuilder.downloader import db

        db.insert_story(
            output_path="/tmp/fields_test.txt",
            title="Test Title",
            author="Test Author",
            story_date="2024-06-01",
            url="http://ex/test",
            content="Test content here",
        )

        result = db.get_story("/tmp/fields_test.txt")

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["title"], "Test Title")
        self.assertIn("Test Author", result["author"])
        self.assertEqual(result["url"], "http://ex/test")
        self.assertIn("Test content", result["content"])


if __name__ == "__main__":
    unittest.main()
