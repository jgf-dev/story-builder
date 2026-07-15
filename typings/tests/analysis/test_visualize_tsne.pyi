from _typeshed import Incomplete

import unittest
from unittest.mock import patch, MagicMock
from storybuilder.analysis.visualize_tsne import main, parse_args


class TestVisualizeTSNE(unittest.TestCase):
    @patch("sys.argv", ["visualize_tsne.py"])
    def test_parse_args_defaults(self) -> None: ...

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
    def test_parse_args_custom(self) -> None: ...

    @patch("storybuilder.analysis.visualize_tsne.chromadb.PersistentClient")
    @patch("storybuilder.analysis.visualize_tsne.pio.write_html")
    @patch("sys.argv", ["visualize_tsne.py", "--perplexity", "2"])
    def test_main(self, mock_write_html: Incomplete, mock_chroma_client: Incomplete) -> None: ...
