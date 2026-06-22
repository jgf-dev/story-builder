import unittest
from unittest.mock import patch
import pandas as pd
import io

from storybuilder.analysis.visualize_arcs import main

class TestVisualizeArcs(unittest.TestCase):
    @patch("sys.argv", ["visualize_arcs.py"])
    @patch("sqlite3.connect")
    @patch("pandas.read_sql_query")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_empty_stories_condition(self, mock_stdout, mock_read_sql_query, mock_connect):
        mock_read_sql_query.return_value = pd.DataFrame()

        main()

        self.assertEqual(mock_stdout.getvalue().strip(), "No processed stories found in DB.")

if __name__ == '__main__':
    unittest.main()
