from _typeshed import Incomplete

import unittest
import sqlite3
import tempfile
import os
from unittest.mock import patch
from storybuilder.analysis.visualize_arcs import main


class TestVisualizeArcs(unittest.TestCase):
    def setUp(self) -> None: ...

    def tearDown(self) -> None: ...

    @patch("sys.argv", ["visualize_arcs.py", "--db-path", ""])
    @patch("plotly.graph_objects.Figure.write_html")
    def test_visualize_arcs(self, mock_write_html: Incomplete) -> None: ...

    @patch("plotly.graph_objects.Figure.write_html")
    def test_visualize_arcs_no_story(self, mock_write_html: Incomplete) -> None: ...

    @patch("sys.stdout.write")
    @patch("plotly.graph_objects.Figure.write_html")
    def test_visualize_arcs_empty_db(self, mock_write_html: Incomplete, mock_stdout: Incomplete) -> None: ...
