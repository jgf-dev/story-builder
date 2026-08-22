from _typeshed import Incomplete

import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from storybuilder.analysis.visualize_arcs import get_top_characters
from storybuilder.analysis.visualize_arcs import main


class TestVisualizeArcs(unittest.TestCase):
    conn: Connection
    cursor: Cursor
    db_path: str
    temp_dir: TemporaryDirectory[str]

    def setUp(self) -> None: ...

    def tearDown(self) -> None: ...

    @patch("sys.argv", ["visualize_arcs.py", "--db-path", ""])
    @patch("plotly.graph_objects.Figure.write_html")
    def test_visualize_arcs(self, mock_write_html: Incomplete) -> None: ...

    def test_get_top_characters(self) -> None: ...

    def test_get_top_characters_limit(self) -> None: ...

    @patch("plotly.graph_objects.Figure.write_html")
    def test_visualize_arcs_no_story(self, mock_write_html: Incomplete) -> None: ...

    @patch("sys.stdout.write")
    @patch("plotly.graph_objects.Figure.write_html")
    def test_visualize_arcs_empty_db(self, mock_write_html: Incomplete, mock_stdout: Incomplete) -> None: ...
