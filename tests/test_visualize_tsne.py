import unittest
from unittest.mock import patch, MagicMock
import sys
import tempfile
import shutil
import os
from io import StringIO
from pathlib import Path

# Add the script directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from storybuilder.analysis.visualize_tsne import main

class TestVisualizeTsne(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_file = os.path.join(self.temp_dir, "test_output.html")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch('storybuilder.analysis.visualize_tsne.chromadb.PersistentClient')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_collection_not_found(self, mock_stdout, mock_client_class):
        # Setup mock to raise Exception when get_collection is called
        mock_client = MagicMock()
        mock_client.get_collection.side_effect = Exception("Collection not found")
        mock_client_class.return_value = mock_client

        # Mock sys.argv
        test_args = ['visualize_tsne.py', '--db-path', self.temp_dir, '--output', self.output_file]
        with patch.object(sys, 'argv', test_args):
            main()

        # Check output
        self.assertIn("Error: Could not find 'story_averages' collection", mock_stdout.getvalue())

    @patch('storybuilder.analysis.visualize_tsne.chromadb.PersistentClient')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_insufficient_data(self, mock_stdout, mock_client_class):
        # Setup mock to return a collection with 1 item
        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["file1.txt"],
            "embeddings": [[0.1, 0.2]],
            "metadatas": [{"key": "value"}]
        }

        mock_client = MagicMock()
        mock_client.get_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client

        # Mock sys.argv
        test_args = ['visualize_tsne.py', '--db-path', self.temp_dir, '--output', self.output_file]
        with patch.object(sys, 'argv', test_args):
            main()

        # Check output
        self.assertIn("Error: Need at least 2 stories in the database to run t-SNE", mock_stdout.getvalue())

    @patch('storybuilder.analysis.visualize_tsne.pio.write_html')
    @patch('storybuilder.analysis.visualize_tsne.chromadb.PersistentClient')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_happy_path(self, mock_stdout, mock_client_class, mock_write_html):
        # Setup mock to return a collection with enough items
        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["cat1/sub1/file1.txt", "cat1/sub2/file2.txt", "cat2/sub3/file3.txt", "cat2/sub4/file4.txt", "file5.txt"],
            "embeddings": [
                [0.1, 0.2, 0.3],
                [0.4, 0.5, 0.6],
                [0.7, 0.8, 0.9],
                [0.1, 0.9, 0.2],
                [0.5, 0.1, 0.8]
            ],
            "metadatas": [{"k": "v"} for _ in range(5)]
        }

        mock_client = MagicMock()
        mock_client.get_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client

        # Mock sys.argv
        test_args = ['visualize_tsne.py', '--db-path', self.temp_dir, '--output', self.output_file, '--perplexity', '2']
        with patch.object(sys, 'argv', test_args):
            main()

        # Check output
        output = mock_stdout.getvalue()
        self.assertIn("Fetching embeddings from database...", output)
        self.assertIn("Loaded 5 story embeddings.", output)
        self.assertIn("Running t-SNE dimensionality reduction", output)
        self.assertIn("Generating interactive plot...", output)
        self.assertIn(f"Visualization saved successfully to {self.output_file}", output)

        # Verify write_html was called with the right filename
        self.assertTrue(mock_write_html.called)
        args, kwargs = mock_write_html.call_args
        self.assertEqual(kwargs.get('file'), self.output_file)

if __name__ == '__main__':
    unittest.main()
