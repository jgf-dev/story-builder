import sys
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

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


if __name__ == "__main__":
    unittest.main()
