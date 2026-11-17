import os
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch


class TestDBInit(unittest.TestCase):
    """Tests for db.init_db and basic schema."""

    def test_init_db_creates_tables(self) -> None:
        """init_db creates the stories and fts tables."""
        import tempfile

        from storybuilder.downloader import db

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

    def test_story_insert_and_search(self) -> None:
        """Basic insert and FTS search roundtrip."""
        import tempfile

        from storybuilder.downloader import db

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

    def test_get_story_by_path(self) -> None:
        """get_story returns story by path."""
        import tempfile

        from storybuilder.downloader import db

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

    def test_story_exists(self) -> None:
        """story_exists checks for path."""
        import tempfile

        from storybuilder.downloader import db

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


if __name__ == "__main__":
    unittest.main()
