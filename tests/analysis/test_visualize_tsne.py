import unittest
from unittest.mock import patch, MagicMock
from storybuilder.analysis.visualize_tsne import main, parse_args


class TestVisualizeTSNE(unittest.TestCase):
    @patch("sys.argv", ["visualize_tsne.py"])
    def test_parse_args_defaults(self) -> None:
        args = parse_args()
        self.assertEqual(args.db_path, "./chroma_db")
        self.assertEqual(args.output, "tsne_visualization.html")
        self.assertEqual(args.perplexity, 1000.0)

    @patch(
        "sys.argv",
        [
            "visualize_tsne.py",
            "--db-path",
            "./custom_db",
            "--output",
            "custom.html",
            "--perplexity",
            "50.5",
        ],
    )
    def test_parse_args_custom(self) -> None:
        args = parse_args()
        self.assertEqual(args.db_path, "./custom_db")
        self.assertEqual(args.output, "custom.html")
        self.assertEqual(args.perplexity, 50.5)

    @patch("storybuilder.analysis.visualize_tsne.chromadb.PersistentClient")
    @patch("storybuilder.analysis.visualize_tsne.pio.write_html")
    @patch("sys.argv", ["visualize_tsne.py", "--perplexity", "2"])
    def test_main(self, mock_write_html, mock_chroma_client) -> None:
        # Setup mock chroma
        mock_client = MagicMock()
        mock_chroma_client.return_value = mock_client
        mock_collection = MagicMock()
        mock_client.get_collection.return_value = mock_collection

        # Mock get() result with 5 samples (more than perplexity=2)
        mock_collection.get.return_value = {
            "ids": [f"story{i}" for i in range(5)],
            "embeddings": [[0.1 * i] * 384 for i in range(5)],
            "metadatas": [{"title": f"Story {i}"} for i in range(5)],
        }

        main()

        # Check if write_html was called. The first argument is the figure object,
        # the second is 'file' (keyword arg in pio.write_html)
        self.assertTrue(mock_write_html.called)
        self.assertEqual(
            mock_write_html.call_args[1]["file"], "tsne_visualization.html"
        )


if __name__ == "__main__":
    unittest.main()
