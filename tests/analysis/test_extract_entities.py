import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import tempfile
import os
from pathlib import Path

from storybuilder.analysis.extract_entities import (
    init_db,
    is_processed,
    main,
)


class TestExtractEntities(unittest.TestCase):
    def setUp(self):
        # Create a temporary database file
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.conn = sqlite3.connect(self.db_path)

        # Create a temporary directory for test text files
        self.stories_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.conn.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)
        self.stories_dir.cleanup()

    def test_init_db(self):
        conn = init_db(self.db_path)
        cursor = conn.cursor()

        # Check if tables were created
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='stories'"
        )
        self.assertIsNotNone(cursor.fetchone())

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='entities'"
        )
        self.assertIsNotNone(cursor.fetchone())

        conn.close()

    def test_is_processed(self):
        conn = init_db(self.db_path)
        cursor = conn.cursor()

        filepath = "test_file.txt"

        # Initially not processed
        self.assertFalse(is_processed(cursor, filepath))

        # Insert a record
        cursor.execute("INSERT INTO stories (filepath) VALUES (?)", (filepath,))
        conn.commit()

        # Now it should be processed
        self.assertTrue(is_processed(cursor, filepath))

        conn.close()

    @patch("argparse.ArgumentParser.parse_args")
    @patch("spacy.load")
    @patch("storybuilder.analysis.extract_entities.require_gpu")
    @patch("storybuilder.analysis.extract_entities.set_gpu_allocator")
    def test_main_happy_path(
        self, mock_set_gpu, mock_require_gpu, mock_spacy_load, mock_parse_args
    ):
        # Setup mocks
        mock_args = MagicMock()
        mock_args.db_path = self.db_path
        mock_args.stories_dir = self.stories_dir.name
        mock_args.limit = 10
        mock_args.force = False
        mock_args.model = "en_core_web_sm"
        mock_args.gpu = False
        mock_parse_args.return_value = mock_args

        mock_nlp = MagicMock()
        mock_spacy_load.return_value = mock_nlp

        # Mock the document returned by spaCy
        mock_doc = MagicMock()
        mock_ent1 = MagicMock()
        mock_ent1.text = "Alice"
        mock_ent1.label_ = "PERSON"
        mock_ent2 = MagicMock()
        mock_ent2.text = "Wonderland"
        mock_ent2.label_ = "LOC"
        mock_doc.ents = [mock_ent1, mock_ent2]
        mock_nlp.return_value = mock_doc

        # Create a dummy text file
        test_file = Path(self.stories_dir.name) / "test1.txt"
        with open(test_file, "w") as f:
            f.write("Alice went to Wonderland.")

        # Run main
        main()

        # Check database contents
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT count(*) FROM stories")
        self.assertEqual(cursor.fetchone()[0], 1)

        cursor.execute("SELECT text, label, frequency FROM entities ORDER BY text")
        entities = cursor.fetchall()
        self.assertEqual(len(entities), 2)
        self.assertEqual(entities[0], ("Alice", "PERSON", 1))
        self.assertEqual(entities[1], ("Wonderland", "LOC", 1))

        conn.close()

    @patch("argparse.ArgumentParser.parse_args")
    @patch("spacy.load")
    def test_main_skip_processed(self, mock_spacy_load, mock_parse_args):
        # Pre-populate db with the file
        test_file_path = str(Path(self.stories_dir.name) / "test1.txt")
        conn = init_db(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO stories (filepath) VALUES (?)", (test_file_path,))
        conn.commit()
        conn.close()

        # Setup mocks
        mock_args = MagicMock()
        mock_args.db_path = self.db_path
        mock_args.stories_dir = self.stories_dir.name
        mock_args.limit = 10
        mock_args.force = False
        mock_args.model = "en_core_web_sm"
        mock_args.gpu = False
        mock_parse_args.return_value = mock_args

        mock_nlp = MagicMock()
        mock_spacy_load.return_value = mock_nlp

        # Create a dummy text file
        with open(test_file_path, "w") as f:
            f.write("Alice went to Wonderland.")

        # Run main
        main()

        # nlp should not have been called because the file was skipped
        mock_nlp.assert_not_called()


if __name__ == "__main__":
    unittest.main()
