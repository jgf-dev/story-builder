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
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
# Also make scripts/ importable (they don't have __init__.py but we can still import
# the modules directly if we add the parent directory)
_scripts_dir = str(Path(__file__).resolve().parents[1] / "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)


class TestParseAuthor(unittest.TestCase):
    """Tests for _parse_author in storybuilder.downloader.db."""

    def test_name_with_email(self):
        from storybuilder.downloader.db import _parse_author
        name, email = _parse_author("John Doe <john@example.com>")
        self.assertEqual(name, "John Doe")
        self.assertEqual(email, "john@example.com")

    def test_bare_email(self):
        from storybuilder.downloader.db import _parse_author
        name, email = _parse_author("anon@test.org")
        self.assertIsNone(name)
        self.assertEqual(email, "anon@test.org")

    def test_name_only(self):
        from storybuilder.downloader.db import _parse_author
        name, email = _parse_author("Jane Austen")
        self.assertEqual(name, "Jane Austen")
        self.assertIsNone(email)

    def test_none_input(self):
        from storybuilder.downloader.db import _parse_author
        name, email = _parse_author(None)
        self.assertIsNone(name)
        self.assertIsNone(email)

    def test_empty_string(self):
        from storybuilder.downloader.db import _parse_author
        name, email = _parse_author("")
        self.assertIsNone(name)
        self.assertIsNone(email)

    def test_name_with_angle_brackets_in_name(self):
        from storybuilder.downloader.db import _parse_author
        name, email = _parse_author("<Special> Author <special@example.com>")
        self.assertEqual(name, "<Special> Author")
        self.assertEqual(email, "special@example.com")


class TestParseOutputPath(unittest.TestCase):
    """Tests for _parse_output_path in storybuilder.downloader.db."""

    def test_multi_chapter_story(self):
        from storybuilder.downloader.db import _parse_output_path
        orientation, category, slug, num = _parse_output_path(
            "nifty_stories/gay/adult-friends/my-story/my-story-3.txt"
        )
        self.assertEqual(orientation, "gay")
        self.assertEqual(category, "adult-friends")
        self.assertEqual(slug, "my-story")
        self.assertEqual(num, 3)

    def test_single_chapter_flat(self):
        from storybuilder.downloader.db import _parse_output_path
        orientation, category, slug, num = _parse_output_path(
            "nifty_stories/gay/adult-friends/my-story.txt"
        )
        self.assertEqual(orientation, "gay")
        self.assertEqual(category, "adult-friends")
        self.assertEqual(slug, "my-story")
        self.assertIsNone(num)

    def test_short_path_fallback(self):
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

    def test_orientation_is_category(self):
        from storybuilder.downloader.db import _parse_output_path
        orientation, category, slug, num = _parse_output_path(
            "nifty_stories/lesbian/college/title/title-1.txt"
        )
        self.assertEqual(orientation, "lesbian")
        self.assertEqual(category, "college")
        self.assertEqual(slug, "title")
        self.assertEqual(num, 1)

    def test_filename_without_chapter(self):
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

    def test_html_file(self):
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

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")

    def tearDown(self):
        # Reset the db module's global connection
        from storybuilder.downloader import db
        db.close_db()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_db_creates_tables(self):
        from storybuilder.downloader.db import init_db, close_db
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

    def test_init_db_creates_indexes(self):
        from storybuilder.downloader.db import init_db, close_db
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

    def test_init_db_has_orientation_column(self):
        from storybuilder.downloader.db import init_db, close_db
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

    def test_init_db_wal_mode(self):
        from storybuilder.downloader.db import init_db, close_db
        conn = init_db(self.db_path)
        try:
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            self.assertEqual(mode.lower(), "wal")
        finally:
            close_db()


class TestInsertStory(unittest.TestCase):
    """Tests for insert_story function."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")

    def tearDown(self):
        from storybuilder.downloader import db
        db.close_db()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_insert_and_retrieve(self):
        from storybuilder.downloader.db import init_db, insert_story, close_db
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
            self.assertEqual(row["path"], "nifty_stories/gay/adult-friends/story-slug/story-slug-1.txt")
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

    def test_insert_no_author(self):
        from storybuilder.downloader.db import init_db, insert_story, close_db
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

    def test_replace_on_duplicate_path(self):
        from storybuilder.downloader.db import init_db, insert_story, close_db
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

    def test_char_and_word_count(self):
        from storybuilder.downloader.db import init_db, insert_story, close_db
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

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")

    def tearDown(self):
        from storybuilder.downloader import db
        db.close_db()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_fts_search_finds_content(self):
        from storybuilder.downloader.db import init_db, insert_story, close_db
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

    def test_fts_update_on_replace(self):
        from storybuilder.downloader.db import init_db, insert_story, close_db
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


class TestParseHeader(unittest.TestCase):
    """Tests for parse_header in import_to_sqlite.py."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_story_file(self, fname, content):
        path = os.path.join(self.temp_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_standard_header(self):
        import import_to_sqlite
        content = (
            "=" * 80 + "\n"
            "Title: My Story\n"
            "Author: Jane Writer <jane@email.com>\n"
            "Publication Date: 2024-06-13\n"
            "URL: https://example.com/story\n"
            + "=" * 80 + "\n\n"
            + "Once upon a time there was a story.\n"
            "It had multiple paragraphs.\n"
        )
        path = self._write_story_file("test.txt", content)
        result = import_to_sqlite.parse_header(path)
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "My Story")
        self.assertEqual(result["author_name"], "Jane Writer")
        self.assertEqual(result["author_email"], "jane@email.com")
        self.assertEqual(result["publication_date"], "2024-06-13")
        self.assertEqual(result["url"], "https://example.com/story")
        self.assertIn("Once upon a time", result["content"])
        self.assertIn("multiple paragraphs", result["content"])

    def test_header_with_email_date(self):
        import import_to_sqlite
        content = (
            "=" * 80 + "\n"
            "Title: Email Story\n"
            "Author: user@host.com\n"
            "Publication Date: 2023-01-01\n"
            "URL: https://example.com\n"
            + "=" * 80 + "\n\n"
            + "Email content here.\n"
        )
        path = self._write_story_file("email.txt", content)
        result = import_to_sqlite.parse_header(path)
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Email Story")
        self.assertIsNone(result["author_name"])
        self.assertEqual(result["author_email"], "user@host.com")

    def test_missing_file(self):
        import import_to_sqlite
        result = import_to_sqlite.parse_header("/nonexistent/file.txt")
        self.assertIsNone(result)

    def test_no_header_marker(self):
        import import_to_sqlite
        content = "Just plain text without any header markers.\n"
        path = self._write_story_file("noheader.txt", content)
        result = import_to_sqlite.parse_header(path)
        self.assertIsNone(result)

    def test_minimal_header(self):
        import import_to_sqlite
        content = (
            "=" * 80 + "\n"
            "Title: Minimal\n"
            "Author: Min\n"
            "Publication Date: 2024-01-01\n"
            "URL: http://x.com\n"
            + "=" * 80 + "\n\n"
            + "body"
        )
        path = self._write_story_file("min.txt", content)
        result = import_to_sqlite.parse_header(path)
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Minimal")
        self.assertEqual(result["content"], "body")

    def test_empty_content(self):
        import import_to_sqlite
        content = (
            "=" * 80 + "\n"
            "Title: Empty\n"
            "Author: Nobody\n"
            "Publication Date: 2024-01-01\n"
            "URL: http://x.com\n"
            + "=" * 80 + "\n\n"
        )
        path = self._write_story_file("empty.txt", content)
        result = import_to_sqlite.parse_header(path)
        # returns None because content is empty and title is there but content is empty string
        # Actually, empty content + title = not None since we check "not content and not title"
        self.assertIsNotNone(result)
        self.assertEqual(result["content"], "")


class TestMultiDBConnect(unittest.TestCase):
    """Tests for connect_multi in story_db.py."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_db(self, fname):
        path = os.path.join(self.temp_dir, fname)
        conn = sqlite3.connect(path)
        conn.execute("""
            CREATE TABLE stories (
                id INTEGER PRIMARY KEY,
                title TEXT,
                word_count INTEGER
            )
        """)
        conn.execute("INSERT INTO stories (title, word_count) VALUES (?, ?)", ("Story A", 100))
        conn.commit()
        conn.close()
        return path

    def test_connect_multi(self):
        import story_db
        self._create_test_db("db1.db")
        self._create_test_db("db2.db")

        conn, db_names = story_db.connect_multi(self.temp_dir)
        self.assertEqual(len(db_names), 2)
        self.assertIn("main", db_names)
        self.assertIn("db1", db_names)
        conn.close()

    def test_query_all(self):
        import story_db
        self._create_test_db("a.db")
        self._create_test_db("b.db")

        conn, db_names = story_db.connect_multi(self.temp_dir)
        try:
            rows = story_db._query_all(
                conn, db_names,
                "SELECT COUNT(*) FROM {table}",
            )
            self.assertEqual(len(rows), 2)
            total = sum(r[0] for r in rows)
            self.assertEqual(total, 2)  # 1 row in each of 2 DBs
        finally:
            conn.close()

    def test_empty_dir_raises(self):
        import story_db
        empty_dir = os.path.join(self.temp_dir, "empty")
        os.makedirs(empty_dir)
        with self.assertRaises(SystemExit):
            story_db.connect_multi(empty_dir)

    def test_skips_stories_db(self):
        import story_db
        self._create_test_db("stories.db")  # should be skipped
        self._create_test_db("real.db")

        conn, db_names = story_db.connect_multi(self.temp_dir)
        self.assertEqual(len(db_names), 1)  # only real.db
        conn.close()
class TestDatabasePartitioning(unittest.TestCase):
    """Tests for year-range partitioning in db.py."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        from storybuilder.downloader import db
        db.close_db()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_partition_path(self):
        from storybuilder.downloader import db
        # Force set the directory
        db._db_dir = "/dummy/dir"
        
        # Strings
        self.assertEqual(os.path.basename(db.get_partition_path("1999-12-31")), "1999.db")
        self.assertEqual(os.path.basename(db.get_partition_path("2000-05-10")), "2000.db")
        self.assertEqual(os.path.basename(db.get_partition_path("2002-05-10")), "2002.db")
        self.assertEqual(os.path.basename(db.get_partition_path("2004-05-10")), "2004.db")
        self.assertEqual(os.path.basename(db.get_partition_path("2007-06-15")), "2007.db")
        self.assertEqual(os.path.basename(db.get_partition_path("2012-08-20")), "2012.db")
        self.assertEqual(os.path.basename(db.get_partition_path("2017-09-25")), "2017.db")
        self.assertEqual(os.path.basename(db.get_partition_path("2022-10-30")), "2022.db")
        self.assertEqual(os.path.basename(db.get_partition_path("2025-05-10")), "2025.db")
        self.assertEqual(os.path.basename(db.get_partition_path("2026-06-12")), "2026.db")
        self.assertEqual(os.path.basename(db.get_partition_path("")), "unknown.db")
        
        # datetime.date objects
        import datetime
        self.assertEqual(os.path.basename(db.get_partition_path(datetime.date(1995, 1, 1))), "1995.db")
        self.assertEqual(os.path.basename(db.get_partition_path(datetime.date(2025, 5, 10))), "2025.db")
        self.assertEqual(os.path.basename(db.get_partition_path(datetime.date(2026, 6, 12))), "2026.db")

    def test_insert_story_partitioned(self):
        from storybuilder.downloader import db
        # Initialize with directory path
        db.init_db(self.temp_dir)
        self.assertTrue(db._is_partitioned)
        self.assertEqual(db._db_dir, self.temp_dir)
        self.assertIsNotNone(db.get_conn())

        # Insert a 2012 story (should route to 2012.db)
        success = db.insert_story(
            output_path="nifty_stories/gay/adult-friends/story1/story1.txt",
            title="2012 Story",
            author="Author One",
            story_date="2012-05-14",
            url="http://example.com/1",
            content="Content for story 1.",
        )
        self.assertTrue(success)

        # Insert a 2025 story (should route to 2025.db)
        success2 = db.insert_story(
            output_path="nifty_stories/gay/college/story2/story2.txt",
            title="2025 Story",
            author="Author Two",
            story_date="2025-05-10",
            url="http://example.com/2",
            content="Content for story 2.",
        )
        self.assertTrue(success2)

        # Insert a 2026 story (should route to 2026.db)
        success3 = db.insert_story(
            output_path="nifty_stories/gay/college/story3/story3.txt",
            title="2026 Story",
            author="Author Three",
            story_date="2026-06-12",
            url="http://example.com/3",
            content="Content for story 3.",
        )
        self.assertTrue(success3)

        # Verify physical files are created in the folder
        db1_path = os.path.join(self.temp_dir, "2012.db")
        db2_path = os.path.join(self.temp_dir, "2025.db")
        db3_path = os.path.join(self.temp_dir, "2026.db")
        self.assertTrue(os.path.exists(db1_path))
        self.assertTrue(os.path.exists(db2_path))
        self.assertTrue(os.path.exists(db3_path))

        # Query them directly to confirm the data was routed correctly
        conn1 = sqlite3.connect(db1_path)
        row1 = conn1.execute("SELECT title, content FROM stories").fetchone()
        self.assertEqual(row1[0], "2012 Story")
        self.assertEqual(row1[1], "Content for story 1.")
        conn1.close()

        conn2 = sqlite3.connect(db2_path)
        row2 = conn2.execute("SELECT title, content FROM stories").fetchone()
        self.assertEqual(row2[0], "2025 Story")
        self.assertEqual(row2[1], "Content for story 2.")
        conn2.close()

        conn3 = sqlite3.connect(db3_path)
        row3 = conn3.execute("SELECT title, content FROM stories").fetchone()
        self.assertEqual(row3[0], "2026 Story")
        self.assertEqual(row3[1], "Content for story 3.")
        conn3.close()


if __name__ == "__main__":
    unittest.main()
