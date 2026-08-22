from _typeshed import Incomplete

import os
import pathlib
import sqlite3
import tempfile
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch
from storybuilder.analysis.analyze_sentiment import extract_chapter_number
from storybuilder.analysis.analyze_sentiment import find_multi_chapter_stories
from storybuilder.analysis.analyze_sentiment import get_sentiment_value
from storybuilder.analysis.analyze_sentiment import init_db
from storybuilder.analysis.analyze_sentiment import main


class TestAnalyzeSentiment(unittest.TestCase):
    def test_get_sentiment_value(self) -> None: ...

    def test_extract_chapter_number(self) -> None: ...

    def test_find_multi_chapter_stories(self) -> None: ...

    def test_init_db(self) -> None: ...

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
    def test_main_no_stories(self, mock_init_db: Incomplete, mock_pipeline: Incomplete, mock_spacy_load: Incomplete) -> None: ...

    @patch("storybuilder.analysis.analyze_sentiment.spacy.load")
    @patch("storybuilder.analysis.analyze_sentiment.pipeline")
    @patch("storybuilder.analysis.analyze_sentiment.init_db")
    @patch(
		"sys.argv",
		["analyze_sentiment.py", "--stories-dir", "fake_dir", "--limit-stories", "1"],
	)
    def test_main_with_stories(self, mock_init_db: Incomplete, mock_pipeline: Incomplete, mock_spacy_load: Incomplete) -> None: ...
