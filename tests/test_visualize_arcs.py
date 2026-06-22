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

        # Insert dummy data
        self.cursor.execute(
            "INSERT INTO stories (id, story_dir) VALUES (1, 'mock_story_dir')"
        )

        # Insert sentences
        for i in range(10):
            self.cursor.execute(
                "INSERT INTO sentences (id, story_id, chapter_index, sentence_index, sentiment_score) VALUES (?, ?, ?, ?, ?)",
                (i, 1, 1, i, 0.5 + (i * 0.05)),
            )

        # Insert entities
        self.cursor.execute(
            "INSERT INTO sentence_entities (sentence_id, entity_text, entity_label) VALUES (1, 'Alice', 'PERSON')"
        )
        self.cursor.execute(
            "INSERT INTO sentence_entities (sentence_id, entity_text, entity_label) VALUES (2, 'Alice', 'PERSON')"
        )
        self.cursor.execute(
            "INSERT INTO sentence_entities (sentence_id, entity_text, entity_label) VALUES (3, 'Bob', 'PERSON')"
        )

        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    @patch("sys.argv", ["visualize_arcs.py", "--db-path", ""])
    @patch("plotly.graph_objects.Figure.write_html")
    def test_visualize_arcs(self, mock_write_html):
        # We need to dynamically patch sys.argv because db_path is generated in setUp
        with patch(
            "sys.argv",
            ["visualize_arcs.py", "--db-path", self.db_path, "--story", "mock"],
        ):
            main()

        mock_write_html.assert_called_once_with("arc_mock_story_dir.html")

    @patch("plotly.graph_objects.Figure.write_html")
    def test_visualize_arcs_no_story(self, mock_write_html):
        with patch("sys.argv", ["visualize_arcs.py", "--db-path", self.db_path]):
            main()

        mock_write_html.assert_called_once_with("arc_mock_story_dir.html")

    @patch("sys.stdout.write")
    @patch("plotly.graph_objects.Figure.write_html")
    def test_visualize_arcs_empty_db(self, mock_write_html, mock_stdout):
        # Create an empty db
        empty_db_path = os.path.join(self.temp_dir.name, "empty.db")
        conn = sqlite3.connect(empty_db_path)
        conn.execute("CREATE TABLE stories (id INTEGER PRIMARY KEY, story_dir TEXT)")
        conn.commit()
        conn.close()

        with patch("sys.argv", ["visualize_arcs.py", "--db-path", empty_db_path]):
            with patch("builtins.print") as mock_print:
                main()
                mock_print.assert_called_with("No processed stories found in DB.")

        mock_write_html.assert_not_called()


if __name__ == "__main__":
    unittest.main()
