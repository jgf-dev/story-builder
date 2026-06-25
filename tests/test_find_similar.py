import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys

from storybuilder.analysis.find_similar import main

class TestFindSimilar(unittest.TestCase):
    @patch('sys.argv', ['find_similar.py', 'test_story.md', '--db-path', '/fake/path'])
    @patch('chromadb.PersistentClient')
    @patch('sys.stdout', new_callable=StringIO)
    def test_collection_not_found(self, mock_stdout, mock_chroma_client):
        # Setup mock client
        mock_instance = MagicMock()
        mock_chroma_client.return_value = mock_instance
        mock_instance.get_collection.side_effect = Exception("Collection not found")

        # Call main
        main()

        # Check output
        output = mock_stdout.getvalue()
        self.assertIn("Error: Could not find 'story_averages' collection", output)

    @patch('sys.argv', ['find_similar.py', 'test_story.md'])
    @patch('chromadb.PersistentClient')
    @patch('sys.stdout', new_callable=StringIO)
    def test_story_not_found(self, mock_stdout, mock_chroma_client):
        mock_instance = MagicMock()
        mock_chroma_client.return_value = mock_instance
        mock_collection = MagicMock()
        mock_instance.get_collection.return_value = mock_collection

        # return empty embeddings
        mock_collection.get.return_value = {"embeddings": []}

        main()

        output = mock_stdout.getvalue()
        self.assertIn("Error: Story 'test_story.md' not found", output)

    @patch('sys.argv', ['find_similar.py', 'target.md', '--n-results', '2'])
    @patch('chromadb.PersistentClient')
    @patch('sys.stdout', new_callable=StringIO)
    def test_success_find_similar(self, mock_stdout, mock_chroma_client):
        mock_instance = MagicMock()
        mock_chroma_client.return_value = mock_instance
        mock_collection = MagicMock()
        mock_instance.get_collection.return_value = mock_collection

        # return embeddings for target
        mock_collection.get.return_value = {"embeddings": [[0.1, 0.2, 0.3]]}

        # return query results
        mock_collection.query.return_value = {
            "ids": [["target.md", "sim1.md", "sim2.md"]],
            "distances": [[0.0, 0.5, 0.6]]
        }

        main()

        output = mock_stdout.getvalue()
        self.assertIn("Finding top 2 stories similar to: target.md", output)
        self.assertNotIn("0. target.md", output) # Should skip itself
        self.assertIn("1. sim1.md", output)
        self.assertIn("2. sim2.md", output)

if __name__ == "__main__":
    unittest.main()
