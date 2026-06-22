import unittest
from unittest.mock import patch, MagicMock
import io
import sys

# Import the main function we want to test
from storybuilder.analysis.find_similar import main


class TestFindSimilar(unittest.TestCase):
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
        captured_output = io.StringIO()
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
        captured_output = io.StringIO()
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
        captured_output = io.StringIO()
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
