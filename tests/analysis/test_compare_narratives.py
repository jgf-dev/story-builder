import io
import shutil
import sqlite3
import sys
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest.mock import patch


# Add the src directory to the python path so we can import the script
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from storybuilder.analysis.compare_narratives import main


class TestCompareNarratives(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.temp_dir) / "test_sentiment.db")
        self.conn = sqlite3.connect(self.db_path)

        # Create necessary tables
        self.conn.execute("""
            CREATE TABLE stories (
                id INTEGER PRIMARY KEY,
                story_dir TEXT,
                subcategory TEXT
            )
        """)
        self.conn.execute("""
            CREATE TABLE sentences (
                story_id INTEGER,
                chapter_index INTEGER,
                sentence_index INTEGER,
                sentiment_score REAL
            )
        """)
        self.conn.commit()

    def tearDown(self) -> None:
        self.conn.close()
        shutil.rmtree(self.temp_dir)

    def test_insufficient_stories(self) -> None:
        # Only add 2 stories
        self.conn.execute(
            "INSERT INTO stories (id, story_dir, subcategory) VALUES (1, 'dir1', 'cat1')"
        )
        self.conn.execute(
            "INSERT INTO stories (id, story_dir, subcategory) VALUES (2, 'dir2', 'cat2')"
        )
        self.conn.commit()

        captured_output = io.StringIO()
        with (
            patch("sys.argv", ["compare_narratives.py", "--db-path", self.db_path]),
            patch("sys.stdout", new=captured_output),
        ):
            main()

        output = captured_output.getvalue()
        self.assertIn("Error: Not enough stories (2) to form 4 clusters.", output)

    def test_skip_short_stories(self) -> None:
        # Add 4 stories
        for i in range(1, 5):
            self.conn.execute(
                "INSERT INTO stories (id, story_dir, subcategory) VALUES (?, ?, ?)",
                (i, f"dir{i}", f"cat{i}"),
            )
            # Add < 20 sentences for each story
            for j in range(10):
                self.conn.execute(
                    """
                    INSERT INTO sentences (story_id, chapter_index, sentence_index, sentiment_score)
                    VALUES (?, ?, ?, ?)
                """,
                    (i, 1, j, 0.5),
                )
        self.conn.commit()

        captured_output = io.StringIO()
        with (
            patch("sys.argv", ["compare_narratives.py", "--db-path", self.db_path]),
            patch("sys.stdout", new=captured_output),
        ):
            main()

        output = captured_output.getvalue()
        self.assertIn("Skipping dir1 (only 10 sentences)", output)
        self.assertIn("No valid trajectories found.", output)

    def test_successful_clustering(self) -> None:
        # Add 4 stories
        for i in range(1, 5):
            self.conn.execute(
                "INSERT INTO stories (id, story_dir, subcategory) VALUES (?, ?, ?)",
                (i, f"dir{i}", f"cat{i}"),
            )
            # Add >= 20 sentences for each story
            # To avoid the ConvergenceWarning of 1 distinct cluster found, make the sentiment scores slightly different per story
            for j in range(25):
                self.conn.execute(
                    """
                    INSERT INTO sentences (story_id, chapter_index, sentence_index, sentiment_score)
                    VALUES (?, ?, ?, ?)
                """,
                    (i, 1, j, 0.1 * (j % 5) + (i * 0.05)),
                )
        self.conn.commit()

        captured_output = io.StringIO()
        with (
            patch(
                "sys.argv",
                ["compare_narratives.py", "--db-path", self.db_path, "--clusters", "2"],
            ),
            patch("plotly.graph_objects.Figure.write_html") as mock_write_html,
            patch("sys.stdout", new=captured_output),
            warnings.catch_warnings(),
        ):
            warnings.simplefilter("ignore")  # Ignore KMeans duplicate warning if any
            main()

        output = captured_output.getvalue()
        self.assertIn("Loaded 4 processed stories. Normalizing trajectories...", output)
        self.assertIn("Clustering into 2 narrative archetypes...", output)
        self.assertIn(
            "Saved archetype visualization to narrative_archetypes.html", output
        )
        mock_write_html.assert_called_once_with("narrative_archetypes.html")


if __name__ == "__main__":
    unittest.main()
