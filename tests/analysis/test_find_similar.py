import sys
import unittest
from io import StringIO
from unittest.mock import MagicMock
from unittest.mock import patch

from storybuilder.analysis.find_similar import main


class TestFindSimilar(unittest.TestCase):
    @patch("sys.stdout", new_callable=StringIO)
    @patch("storybuilder.analysis.find_similar.chromadb.PersistentClient")
    @patch("sys.argv", ["find_similar.py", "test_story.txt"])
    def test_missing_collection_error(self, mock_client_class, mock_stdout):
        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Simulate getting collection throwing an exception
        mock_client.get_collection.side_effect = Exception("Collection not found")

        # Run main
        main()

        # Assertions
        mock_client.get_collection.assert_called_once_with(name="story_averages")

        output = mock_stdout.getvalue()
        self.assertIn(
            "Error: Could not find 'story_averages' collection. Run generate_embeddings.py first.",
            output,
        )

    @patch("storybuilder.analysis.find_similar.chromadb.PersistentClient")
    @patch("storybuilder.analysis.find_similar.argparse.ArgumentParser.parse_args")
    def test_missing_story_result_none(self, mock_parse_args, mock_chroma_client):
        # Setup mock args
        mock_args = MagicMock()
        mock_args.target_story = "nonexistent_story.txt"
        mock_args.db_path = "./chroma_db"
        mock_args.n_results = 5
        mock_parse_args.return_value = mock_args

        # Setup mock chroma client and collection
        mock_client_instance = MagicMock()
        mock_chroma_client.return_value = mock_client_instance

        mock_collection = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection

        # Mock the get result to return None
        mock_collection.get.return_value = None

        # Capture print output
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            main()
        finally:
            sys.stdout = sys.__stdout__

        # Assert output contains the expected error message
        output = captured_output.getvalue()
        self.assertIn(
            "Error: Story 'nonexistent_story.txt' not found in the database.", output
        )

    @patch("storybuilder.analysis.find_similar.chromadb.PersistentClient")
    @patch("storybuilder.analysis.find_similar.argparse.ArgumentParser.parse_args")
    def test_missing_story_embeddings_none(self, mock_parse_args, mock_chroma_client):
        # Setup mock args
        mock_args = MagicMock()
        mock_args.target_story = "nonexistent_story.txt"
        mock_args.db_path = "./chroma_db"
        mock_args.n_results = 5
        mock_parse_args.return_value = mock_args

        # Setup mock chroma client and collection
        mock_client_instance = MagicMock()
        mock_chroma_client.return_value = mock_client_instance

        mock_collection = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection

        # Mock the get result to return dict with None embeddings
        mock_collection.get.return_value = {"embeddings": None}

        # Capture print output
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            main()
        finally:
            sys.stdout = sys.__stdout__

        # Assert output contains the expected error message
        output = captured_output.getvalue()
        self.assertIn(
            "Error: Story 'nonexistent_story.txt' not found in the database.", output
        )

    @patch("storybuilder.analysis.find_similar.chromadb.PersistentClient")
    @patch("storybuilder.analysis.find_similar.argparse.ArgumentParser.parse_args")
    def test_missing_story_embeddings_empty_list(
        self, mock_parse_args, mock_chroma_client
    ):
        # Setup mock args
        mock_args = MagicMock()
        mock_args.target_story = "nonexistent_story.txt"
        mock_args.db_path = "./chroma_db"
        mock_args.n_results = 5
        mock_parse_args.return_value = mock_args

        # Setup mock chroma client and collection
        mock_client_instance = MagicMock()
        mock_chroma_client.return_value = mock_client_instance

        mock_collection = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection

        # Mock the get result to return dict with empty embeddings list
        mock_collection.get.return_value = {"embeddings": []}

        # Capture print output
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            main()
        finally:
            sys.stdout = sys.__stdout__

        # Assert output contains the expected error message
        output = captured_output.getvalue()
        self.assertIn(
            "Error: Story 'nonexistent_story.txt' not found in the database.", output
        )


if __name__ == "__main__":
    unittest.main()
