import unittest
import tempfile
import os
import shutil
import sqlite3

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

    def test_optimize_fts_all(self):
        from storybuilder.downloader import db
        # Initialize with directory path
        db.init_db(self.temp_dir)

        # Insert stories to create multiple partition DBs
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

        # We need to simulate that `optimize_fts` will process all databases in `self.temp_dir`.
        db.optimize_fts()

        # Since FTS optimization runs PRAGMA equivalent or just executes an INSERT on a virtual table,
        # verifying execution isn't as simple as checking a flag. But we can ensure no errors are
        # raised, and that we can still search afterwards.

        conn1 = sqlite3.connect(os.path.join(self.temp_dir, "2012.db"))
        row1 = conn1.execute("SELECT COUNT(*) FROM stories_fts WHERE stories_fts MATCH 'Content'").fetchone()[0]
        self.assertEqual(row1, 1)
        conn1.close()

        conn2 = sqlite3.connect(os.path.join(self.temp_dir, "2025.db"))
        row2 = conn2.execute("SELECT COUNT(*) FROM stories_fts WHERE stories_fts MATCH 'Content'").fetchone()[0]
        self.assertEqual(row2, 1)
        conn2.close()


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
        import sys; import os; sys.path.insert(0, os.path.abspath('scripts')); import story_db
        self._create_test_db("db1.db")
        self._create_test_db("db2.db")

        conn, db_paths = story_db.connect_multi(self.temp_dir)
        self.assertEqual(len(db_paths), 2)
        self.assertTrue(any("db1.db" in p for p in db_paths))
        self.assertTrue(any("db2.db" in p for p in db_paths))
        conn.close()

    def test_query_all(self):
        import sys; import os; sys.path.insert(0, os.path.abspath('scripts')); import story_db
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
        import sys; import os; sys.path.insert(0, os.path.abspath('scripts')); import story_db
        empty_dir = os.path.join(self.temp_dir, "empty")
        os.makedirs(empty_dir)
        with self.assertRaises(SystemExit):
            story_db.connect_multi(empty_dir)

    def test_skips_stories_db(self):
        import sys; import os; sys.path.insert(0, os.path.abspath('scripts')); import story_db
        self._create_test_db("stories.db")  # should be skipped
        self._create_test_db("real.db")

        conn, db_paths = story_db.connect_multi(self.temp_dir)
        self.assertEqual(len(db_paths), 1)  # only real.db
        self.assertTrue(any("real.db" in p for p in db_paths))
        conn.close()

class TestImportToSQLite(unittest.TestCase):
    def _write_story_file(self, filename, content):
        path = os.path.join(self.temp_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_header_valid(self):
        import sys; import os; sys.path.insert(0, os.path.abspath('scripts')); import import_to_sqlite
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
        self.assertEqual(result["content"], "This is the body of the story.\nIt has multiple lines.")

    def test_parse_header_missing_fields(self):
        import sys; import os; sys.path.insert(0, os.path.abspath('scripts')); import import_to_sqlite
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

    def test_parse_header_invalid_format(self):
        import sys; import os; sys.path.insert(0, os.path.abspath('scripts')); import import_to_sqlite
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

    def test_minimal_header(self):
        import sys; import os; sys.path.insert(0, os.path.abspath('scripts')); import import_to_sqlite
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
        import sys; import os; sys.path.insert(0, os.path.abspath('scripts')); import import_to_sqlite
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

if __name__ == "__main__":
    unittest.main()
