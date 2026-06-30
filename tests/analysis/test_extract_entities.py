import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

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
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stories'")
        self.assertIsNotNone(cursor.fetchone())

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entities'")
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

    @patch('argparse.ArgumentParser.parse_args')
    @patch('spacy.load')
    @patch('storybuilder.analysis.extract_entities.require_gpu')
    @patch('storybuilder.analysis.extract_entities.set_gpu_allocator')
    def test_main_happy_path(self, mock_set_gpu, mock_require_gpu, mock_spacy_load, mock_parse_args):
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

    @patch('argparse.ArgumentParser.parse_args')
    @patch('spacy.load')
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

    @patch('argparse.ArgumentParser.parse_args')
    @patch('spacy.load')
    def test_main_force_reprocess(self, mock_spacy_load, mock_parse_args):
        # Pre-populate db with the file and an old entity
        test_file_path = str(Path(self.stories_dir.name) / "test1.txt")
        conn = init_db(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO stories (id, filepath) VALUES (1, ?)", (test_file_path,))
        cursor.execute("INSERT INTO entities (story_id, text, label, frequency) VALUES (1, 'OldEntity', 'PERSON', 5)")
        conn.commit()
        conn.close()

        # Setup mocks
        mock_args = MagicMock()
        mock_args.db_path = self.db_path
        mock_args.stories_dir = self.stories_dir.name
        mock_args.limit = 10
        mock_args.force = True  # force is True
        mock_args.model = "en_core_web_sm"
        mock_args.gpu = False
        mock_parse_args.return_value = mock_args

        mock_nlp = MagicMock()
        mock_spacy_load.return_value = mock_nlp

        mock_doc = MagicMock()
        mock_ent1 = MagicMock()
        mock_ent1.text = "NewEntity"
        mock_ent1.label_ = "PERSON"
        mock_doc.ents = [mock_ent1]
        mock_nlp.return_value = mock_doc

        # Create a dummy text file
        with open(test_file_path, "w") as f:
            f.write("NewEntity is here.")

        # Run main
        main()

        # Check database contents - Old entity should be gone, new one should be present
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT count(*) FROM stories")
        self.assertEqual(cursor.fetchone()[0], 1)

        cursor.execute("SELECT text, label, frequency FROM entities")
        entities = cursor.fetchall()
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0], ("NewEntity", "PERSON", 1))

        conn.close()

    @patch("argparse.ArgumentParser.parse_args")
    @patch("spacy.load")
    def test_main_model_not_found(self, mock_spacy_load, mock_parse_args):
        # Setup mocks to raise OSError
        mock_args = MagicMock()
        mock_args.db_path = self.db_path
        mock_args.model = "en_core_web_sm"
        mock_args.force = False
        mock_args.gpu = False
        mock_parse_args.return_value = mock_args

        mock_spacy_load.side_effect = OSError("Model not found")

        # Capture print output
        with patch("builtins.print") as mock_print:
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 1)

        mock_print.assert_any_call("Model 'en_core_web_sm' not found.")
        mock_print.assert_any_call("Please run: python -m spacy download en_core_web_sm")

    @patch('argparse.ArgumentParser.parse_args')
    @patch('spacy.load')
    @patch('storybuilder.analysis.extract_entities.require_gpu')
    @patch('storybuilder.analysis.extract_entities.set_gpu_allocator')
    @patch('spacy.require_gpu')
    def test_main_with_gpu(self, mock_spacy_require_gpu, mock_set_gpu, mock_require_gpu, mock_spacy_load, mock_parse_args):
        # Setup mocks
        mock_args = MagicMock()
        mock_args.db_path = self.db_path
        mock_args.stories_dir = self.stories_dir.name
        mock_args.limit = 10
        mock_args.force = False
        mock_args.model = "en_core_web_sm"
        mock_args.gpu = True # GPU enabled
        mock_parse_args.return_value = mock_args

        mock_nlp = MagicMock()
        mock_spacy_load.return_value = mock_nlp

        # Mock the document returned by spaCy
        mock_doc = MagicMock()
        mock_ent1 = MagicMock()
        mock_ent1.text = "Alice"
        mock_ent1.label_ = "PERSON"
        mock_doc.ents = [mock_ent1]
        mock_nlp.return_value = mock_doc

        # Create a dummy text file
        test_file = Path(self.stories_dir.name) / "test1.txt"
        with open(test_file, "w") as f:
            f.write("Alice went to Wonderland.")

        # Run main
        main()

        # Verify GPU functions were called
        mock_set_gpu.assert_called_with("pytorch")
        mock_require_gpu.assert_called_with(0)
        mock_spacy_require_gpu.assert_called()

    @patch('argparse.ArgumentParser.parse_args')
    @patch('spacy.load')
    def test_main_error_processing_file(self, mock_spacy_load, mock_parse_args):
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
        # Have nlp raise an exception
        mock_nlp.side_effect = Exception("Simulated error processing file")
        mock_spacy_load.return_value = mock_nlp

        # Create a dummy text file
        test_file = Path(self.stories_dir.name) / "test_error.txt"
        with open(test_file, "w") as f:
            f.write("Text that causes an error.")

        # Capture print output
        with patch('builtins.print') as mock_print:
            main()

        # The file processing should fail gracefully and print an error message
        # Let's check if there is an error message printed
        found_error = False
        for call in mock_print.call_args_list:
            if "Error processing" in str(call):
                found_error = True
                break

        self.assertTrue(found_error)

        # Check database contents - No file should be processed
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT count(*) FROM stories")
        self.assertEqual(cursor.fetchone()[0], 0)

        conn.close()


@patch("storybuilder.analysis.extract_entities.spacy.load")
@patch("storybuilder.analysis.extract_entities.spacy.require_gpu")
@patch("storybuilder.analysis.extract_entities.require_gpu")
@patch("storybuilder.analysis.extract_entities.set_gpu_allocator")
def test_load_spacy_model_with_gpu(
    self,
    mock_set_gpu_allocator,
    mock_require_gpu_thinc,
    mock_require_gpu_spacy,
    mock_spacy_load,
):
    from storybuilder.analysis.extract_entities import load_spacy_model
    # Setup mock nlp object
    mock_nlp = MagicMock()
    mock_spacy_load.return_value = mock_nlp

    # Call function
    result = load_spacy_model("en_core_web_lg", True)

    # Assertions
    mock_set_gpu_allocator.assert_called_once_with("pytorch")
    mock_require_gpu_thinc.assert_called_once_with(0)
    mock_require_gpu_spacy.assert_called_once()
    mock_spacy_load.assert_called_once_with("en_core_web_lg")

    mock_nlp.select_pipes.assert_called_once_with(
        enable=["tagger", "parser", "ner"]
    )
    mock_nlp.add_pipe.assert_any_call("merge_noun_chunks")
    mock_nlp.add_pipe.assert_any_call("merge_entities")
    self.assertEqual(mock_nlp.max_length, 5000000)

    self.assertEqual(result, mock_nlp)

@patch("storybuilder.analysis.extract_entities.spacy.load")
@patch("storybuilder.analysis.extract_entities.spacy.require_gpu")
@patch("storybuilder.analysis.extract_entities.require_gpu")
@patch("storybuilder.analysis.extract_entities.set_gpu_allocator")
def test_load_spacy_model_without_gpu(
    self,
    mock_set_gpu_allocator,
    mock_require_gpu_thinc,
    mock_require_gpu_spacy,
    mock_spacy_load,
):
    from storybuilder.analysis.extract_entities import load_spacy_model
    # Setup mock nlp object
    mock_nlp = MagicMock()
    mock_spacy_load.return_value = mock_nlp

    # Call function
    result = load_spacy_model("en_core_web_lg", False)

    # Assertions
    mock_set_gpu_allocator.assert_not_called()
    mock_require_gpu_thinc.assert_not_called()
    mock_require_gpu_spacy.assert_not_called()
    mock_spacy_load.assert_called_once_with("en_core_web_lg")

    mock_nlp.select_pipes.assert_called_once_with(
        enable=["tagger", "parser", "ner"]
    )
    mock_nlp.add_pipe.assert_any_call("merge_noun_chunks")
    mock_nlp.add_pipe.assert_any_call("merge_entities")
    self.assertEqual(mock_nlp.max_length, 5000000)

    self.assertEqual(result, mock_nlp)

@patch("builtins.print")
@patch("storybuilder.analysis.extract_entities.spacy.load")
def test_load_spacy_model_oserror(self, mock_spacy_load, mock_print):
    from storybuilder.analysis.extract_entities import load_spacy_model
    # Setup mock to raise OSError
    mock_spacy_load.side_effect = OSError("Model not found")

    # Call function
    result = load_spacy_model("en_core_web_lg", False)

    # Assertions
    mock_spacy_load.assert_called_once_with("en_core_web_lg")
    mock_print.assert_any_call("Model 'en_core_web_lg' not found.")
    mock_print.assert_any_call(
        "Please run: python -m spacy download en_core_web_lg"
    )
    self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()