import unittest
import tempfile
import shutil
import os
import sqlite3
from unittest.mock import patch, MagicMock


class TestDBInit(unittest.TestCase):
    """Tests for db.init_db and basic schema."""

    def test_init_db_creates_tables(self):
        """init_db creates the stories and fts tables."""
        from storybuilder.downloader import db
        import tempfile

        temp_dir = tempfile.mkdtemp()
        try:
            db_path = os.path.join(temp_dir, "test.db")
            conn = db.init_db(db_path)

            # Check tables exist
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}

            self.assertIn("stories", tables)
            self.assertIn("stories_fts", tables)  # FTS5 virtual table

            conn.close()
        finally:
            shutil.rmtree(temp_dir)

    def test_story_insert_and_search(self):
        """Basic insert and FTS search roundtrip."""
        from storybuilder.downloader import db
        import tempfile

        temp_dir = tempfile.mkdtemp()
        try:
            db_path = os.path.join(temp_dir, "test.db")
            conn = db.init_db(db_path)

            # Insert a story (note: uses output_path, not path)
            result = db.insert_story(
                output_path="/tmp/story.txt",
                title="Test",
                author="Author",
                story_date="2024-06-01",
                url="http://ex",
                content="Test story about love",
            )
            self.assertTrue(result)

            # Search works
            results = db.search_stories("love")
            self.assertGreater(len(results), 0)
            self.assertEqual(results[0]["title"], "Test")

            conn.close()
        finally:
            shutil.rmtree(temp_dir)


class TestDBExport(unittest.TestCase):
    """Tests for export functionality."""

    def test_get_story_by_path(self):
        """get_story returns story by path."""
        from storybuilder.downloader import db
        import tempfile

        temp_dir = tempfile.mkdtemp()
        try:
            db_path = os.path.join(temp_dir, "test.db")
            conn = db.init_db(db_path)

            db.insert_story(
                output_path="/tmp/exact.txt",
                title="Test",
                author="A",
                story_date="2024-06-01",
                url="http://ex",
                content="Content",
            )

            story = db.get_story("/tmp/exact.txt")
            self.assertIsNotNone(story)
            self.assertEqual(story["title"], "Test")

            conn.close()
        finally:
            shutil.rmtree(temp_dir)

    def test_story_exists(self):
        """story_exists checks for path."""
        from storybuilder.downloader import db
        import tempfile

        temp_dir = tempfile.mkdtemp()
        try:
            db_path = os.path.join(temp_dir, "test.db")
            conn = db.init_db(db_path)

            db.insert_story(
                output_path="/tmp/exists.txt",
                title="Test",
                author="A",
                story_date="2024-06-01",
                url="http://ex",
                content="x",
            )

            self.assertTrue(db.story_exists("/tmp/exists.txt"))
            self.assertFalse(db.story_exists("/tmp/notthere.txt"))

            conn.close()
        finally:
            shutil.rmtree(temp_dir)


class TestDBPartitionPaths(unittest.TestCase):
    """Tests for get_all_partition_paths."""

    def test_get_all_partition_paths_returns_list(self):
        """Returns a list of partition path strings."""
        from storybuilder.downloader import db

        paths = db.get_all_partition_paths()
        self.assertIsInstance(paths, list)


if __name__ == "__main__":
    unittest.main()