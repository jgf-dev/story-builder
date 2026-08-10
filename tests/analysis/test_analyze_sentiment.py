import unittest
import tempfile
import os
import sqlite3
from unittest.mock import patch, MagicMock

from storybuilder.analysis.analyze_sentiment import (
	extract_chapter_number,
	get_sentiment_value,
	init_db,
	main,
)


class TestAnalyzeSentiment(unittest.TestCase):
	def test_get_sentiment_value(self) -> None:
		# Positive sentiment
		self.assertEqual(get_sentiment_value({"label": "POSITIVE", "score": 0.9}), 0.9)
		self.assertEqual(get_sentiment_value({"label": "positive", "score": 0.5}), 0.5)

		# Negative sentiment
		self.assertEqual(get_sentiment_value({"label": "NEGATIVE", "score": 0.8}), -0.8)
		self.assertEqual(get_sentiment_value({"label": "negative", "score": 0.2}), -0.2)

		# Neutral / Other sentiment
		self.assertEqual(get_sentiment_value({"label": "NEUTRAL", "score": 0.9}), 0.0)
		self.assertEqual(get_sentiment_value({"label": "unknown", "score": 0.1}), 0.0)

	def test_extract_chapter_number(self) -> None:
		self.assertEqual(extract_chapter_number("story-name-12.txt"), 12)
		self.assertEqual(extract_chapter_number("story-name-1.txt"), 1)
		self.assertEqual(extract_chapter_number("chapter4.txt"), 4)
		self.assertEqual(extract_chapter_number("042.txt"), 42)
		self.assertEqual(extract_chapter_number("some_random_text.txt"), 0)
		self.assertEqual(extract_chapter_number("no_numbers_here.txt"), 0)

	def test_init_db(self) -> None:
		with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
			db_path = tmp.name

		try:
			conn = init_db(db_path)
			self.assertIsInstance(conn, sqlite3.Connection)

			cursor = conn.cursor()

			# Check if tables are created
			cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
			tables = {row[0] for row in cursor.fetchall()}
			self.assertIn("stories", tables)
			self.assertIn("sentences", tables)
			self.assertIn("sentence_entities", tables)

			# Check if indices are created
			cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
			indices = {row[0] for row in cursor.fetchall()}
			self.assertIn("idx_sentences_story", indices)
			self.assertIn("idx_entities_sentence", indices)
			self.assertIn("idx_entities_text", indices)

			conn.close()
		finally:
			if os.path.exists(db_path):
				os.remove(db_path)

	@patch("storybuilder.analysis.analyze_sentiment.spacy.load")
	@patch("storybuilder.analysis.analyze_sentiment.pipeline")
	@patch("storybuilder.analysis.analyze_sentiment.init_db")
	@patch(
		"sys.argv",
		[
			"analyze_sentiment.py",
			"--stories-dir",
			"fake_dir",
			"--limit-stories",
			"1",
			"--gpu",
		],
	)
	def test_main_no_stories(self, mock_init_db, mock_pipeline, mock_spacy_load) -> None:
		# When no stories exist, main should just return early.
		with patch("pathlib.Path.rglob", return_value=[]):
			main()
			mock_init_db.assert_not_called()

	@patch("storybuilder.analysis.analyze_sentiment.spacy.load")
	@patch("storybuilder.analysis.analyze_sentiment.pipeline")
	@patch("storybuilder.analysis.analyze_sentiment.init_db")
	@patch(
		"sys.argv",
		["analyze_sentiment.py", "--stories-dir", "fake_dir", "--limit-stories", "1"],
	)
	def test_main_with_stories(self, mock_init_db, mock_pipeline, mock_spacy_load) -> None:
		# Create a mock database connection
		mock_conn = MagicMock()
		mock_cursor = MagicMock()
		mock_conn.cursor.return_value = mock_cursor
		mock_init_db.return_value = mock_conn

		# When querying stories, return None to simulate story not processed
		mock_cursor.fetchone.return_value = None
		mock_cursor.lastrowid = 1

		# Setup fake paths
		from pathlib import Path

		fake_files = [
			Path("fake_dir/cat1/story1/story1-1.txt"),
			Path("fake_dir/cat1/story1/story1-2.txt"),
		]

		# Mock spacy
		mock_nlp = MagicMock()
		mock_spacy_load.return_value = mock_nlp

		mock_doc = MagicMock()
		mock_sent = MagicMock()
		mock_sent.text = "This is a sentence."

		mock_ent = MagicMock()
		mock_ent.text = "John"
		mock_ent.label_ = "PERSON"
		mock_sent.ents = [mock_ent]

		mock_doc.sents = [mock_sent]
		mock_nlp.return_value = mock_doc

		# Mock pipeline
		mock_pipe_instance = MagicMock()
		mock_pipe_instance.return_value = [{"label": "POSITIVE", "score": 0.99}]
		mock_pipeline.return_value = mock_pipe_instance

		from unittest.mock import mock_open

		with (
			patch("pathlib.Path.rglob", return_value=fake_files),
			patch("builtins.open", mock_open(read_data="This is a sentence.")),
		):
			main()

		mock_init_db.assert_called_once()
		self.assertTrue(mock_cursor.execute.called)
		self.assertTrue(mock_conn.commit.called)
		mock_conn.close.assert_called_once()


if __name__ == "__main__":
	unittest.main()
