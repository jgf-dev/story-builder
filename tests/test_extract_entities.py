import unittest
from unittest.mock import patch, MagicMock
import sys
from io import StringIO
from contextlib import redirect_stdout
from storybuilder.analysis.extract_entities import main

class TestExtractEntities(unittest.TestCase):
    @patch("sys.argv", ["extract_entities.py", "--model", "non_existent_model"])
    @patch("storybuilder.analysis.extract_entities.spacy.load")
    @patch("storybuilder.analysis.extract_entities.init_db")
    @patch("storybuilder.analysis.extract_entities.set_gpu_allocator")
    @patch("storybuilder.analysis.extract_entities.require_gpu")
    @patch("storybuilder.analysis.extract_entities.spacy.require_gpu")
    def test_missing_spacy_model(self, mock_spacy_require_gpu, mock_require_gpu, mock_set_gpu_allocator, mock_init_db, mock_spacy_load):
        # Setup the mock for init_db to avoid creating a real database
        mock_conn = MagicMock()
        mock_init_db.return_value = mock_conn

        # Setup the mock for spacy.load to raise OSError
        mock_spacy_load.side_effect = OSError("Can't find model 'non_existent_model'")

        # Capture stdout
        captured_output = StringIO()

        with redirect_stdout(captured_output):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 1)

        # Verify output
        output = captured_output.getvalue()
        self.assertIn("Model 'non_existent_model' not found. Please run: python -m spacy download non_existent_model", output)

        # Verify spacy.load was called with the model name from argv
        mock_spacy_load.assert_called_once_with("non_existent_model")

if __name__ == "__main__":
    unittest.main()
