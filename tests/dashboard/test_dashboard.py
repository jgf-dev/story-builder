#!/usr/bin/env python3
"""Tests for the Streamlit dashboard queries and metadata utilities."""

import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


# Ensure src and scripts are importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
_scripts_dir = str(Path(__file__).resolve().parents[2] / "scripts")
if _scripts_dir not in sys.path:
	sys.path.insert(0, _scripts_dir)

import dashboard  # pyrefly: ignore [missing-import]


class TestDashboard(unittest.TestCase):
	"""Tests for the main dashboard logic in scripts/dashboard.py."""

	def setUp(self) -> None:
		self.temp_dir = tempfile.mkdtemp()
		self.db_dir = os.path.join(self.temp_dir, "db")
		Path(self.db_dir).mkdir(exist_ok=True, parents=True)

		self.nlp_db_path = os.path.join(self.temp_dir, "nlp_analysis.db")
		self.meta_db_path = os.path.join(self.temp_dir, "dashboard_metadata.db")

		# Clear Streamlit cache to prevent state pollution
		import streamlit as st

		st.cache_data.clear()

		# Patch paths inside dashboard
		self.patch_dir = patch("dashboard.DB_DIR", self.db_dir)
		self.patch_nlp = patch("dashboard.NLP_DB_PATH", self.nlp_db_path)
		self.patch_meta = patch("dashboard.META_DB_PATH", self.meta_db_path)

		# Patch db.py globals used by dashboard's new refactored code
		import storybuilder.downloader.db as sb_db

		sb_db.init_db(self.db_dir)

		self.patch_dir.start()
		self.patch_nlp.start()
		self.patch_meta.start()

	def tearDown(self) -> None:
		self.patch_dir.stop()
		self.patch_nlp.stop()
		self.patch_meta.stop()
		shutil.rmtree(self.temp_dir, ignore_errors=True)

	def _create_mock_partition(
		self,
		year,
		category,
		title,
		author,
		date,
		word_count,
		path,
		content,
	) -> None:
		from sqlmodel import Session
		from sqlmodel import select

		from storybuilder.downloader import db as sb_db

		sb_db.insert_story(
			output_path=path,
			title=title,
			author=author,
			story_date=date,
			url="http://test",
			content=content,
		)
		if word_count is not None:
			with Session(sb_db._engine) as session:
				story = session.exec(select(sb_db.Story).where(sb_db.Story.path == path)).first()
				if story:
					story.word_count = word_count
					session.add(story)
					session.commit()

	def _create_mock_nlp_db(self, filepath, text, label) -> None:
		conn = sqlite3.connect(self.nlp_db_path)
		conn.execute(
			"""
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT UNIQUE,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
		)
		conn.execute(
			"""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id INTEGER,
                text TEXT,
                label TEXT,
                frequency INTEGER,
                FOREIGN KEY(story_id) REFERENCES stories(id)
            )
            """,
		)
		conn.execute(
			"INSERT OR REPLACE INTO stories (filepath) VALUES (?)",
			(filepath,),
		)
		story_id = conn.execute(
			"SELECT id FROM stories WHERE filepath = ?",
			(filepath,),
		).fetchone()[0]
		conn.execute(
			"INSERT INTO entities (story_id, text, label, frequency) VALUES (?, ?, ?, 1)",
			(story_id, text, label),
		)

		conn.commit()
		conn.close()

	def test_get_db_files(self) -> None:
		from dashboard import get_db_files  # pyrefly: ignore [missing-import]

		self.assertEqual(get_db_files(), [])

		# Create mock db files
		Path(os.path.join(self.db_dir, "2025.db")).open("w").close()
		Path(os.path.join(self.db_dir, "2026.db")).open("w").close()

		files = [os.path.basename(f) for f in get_db_files()]
		self.assertEqual(files, ["2025.db", "2026.db"])

	def test_favorites_crud(self) -> None:
		from dashboard import add_favorite  # pyrefly: ignore [missing-import]
		from dashboard import get_favorites  # pyrefly: ignore [missing-import]
		from dashboard import remove_favorite  # pyrefly: ignore [missing-import]

		# Initial empty
		self.assertEqual(get_favorites(), [])

		# Add favorite
		success = add_favorite(
			"test_path.txt",
			"Test Story",
			"Test Author",
			"tag1,tag2",
			"Some notes",
		)
		self.assertTrue(success)

		favs = get_favorites()
		self.assertEqual(len(favs), 1)
		self.assertEqual(favs[0]["story_path"], "test_path.txt")
		self.assertEqual(favs[0]["title"], "Test Story")
		self.assertEqual(favs[0]["tags"], "tag1,tag2")
		self.assertEqual(favs[0]["notes"], "Some notes")

		# Update favorite
		success_update = add_favorite(
			"test_path.txt",
			"Test Story",
			"Test Author",
			"tag1,tag2,tag3",
			"Updated notes",
		)
		self.assertTrue(success_update)
		favs = get_favorites()
		self.assertEqual(favs[0]["tags"], "tag1,tag2,tag3")
		self.assertEqual(favs[0]["notes"], "Updated notes")

		# Remove favorite
		success_remove = remove_favorite("test_path.txt")
		self.assertTrue(success_remove)
		self.assertEqual(get_favorites(), [])

	def test_query_stories_metadata(self) -> None:
		from dashboard import query_stories  # pyrefly: ignore [missing-import]

		# Create stories in different partitions
		self._create_mock_partition(
			year=2025,
			category="college",
			title="2025 Story Title",
			author="Author Alpha",
			date="2025-05-10",
			word_count=500,
			path="nifty_stories/gay/college/story1.txt",
			content="This is the content of story one.",
		)

		self._create_mock_partition(
			year=2026,
			category="athletics",
			title="2026 Story Title",
			author="Author Beta",
			date="2026-06-12",
			word_count=1200,
			path="nifty_stories/gay/athletics/story2.txt",
			content="This is the content of story two containing werewolf words.",
		)

		# Browse all
		results = query_stories()
		self.assertEqual(len(results), 2)
		# Results should be sorted by date desc
		self.assertEqual(results[0]["title"], "2026 Story Title")
		self.assertEqual(results[1]["title"], "2025 Story Title")

		# Filter by category
		res_cat = query_stories(category="college")
		self.assertEqual(len(res_cat), 1)
		self.assertEqual(res_cat[0]["title"], "2025 Story Title")

		# Filter by author
		res_auth = query_stories(author="Author Beta")
		self.assertEqual(len(res_auth), 1)
		self.assertEqual(res_auth[0]["title"], "2026 Story Title")

		# Filter by year range
		res_year = query_stories(year_range=(2025, 2025))
		self.assertEqual(len(res_year), 1)
		self.assertEqual(res_year[0]["title"], "2025 Story Title")

	def test_query_stories_fts(self) -> None:
		from dashboard import query_stories  # pyrefly: ignore [missing-import]

		self._create_mock_partition(
			year=2026,
			category="athletics",
			title="Wolverine vs Werewolf",
			author="Author Beta",
			date="2026-06-12",
			word_count=1200,
			path="nifty_stories/gay/athletics/story2.txt",
			content="This is the content of story two containing werewolf words.",
		)

		# FTS query match
		res_fts = query_stories(fts_query="werewolf")
		self.assertEqual(len(res_fts), 1)
		self.assertEqual(res_fts[0]["title"], "Wolverine vs Werewolf")

		# FTS query no match
		res_no_match = query_stories(fts_query="vampire")
		self.assertEqual(len(res_no_match), 0)

	def test_query_stories_with_entities(self) -> None:
		from dashboard import query_stories  # pyrefly: ignore [missing-import]

		story_path = "nifty_stories/gay/college/story1.txt"
		self._create_mock_partition(
			year=2025,
			category="college",
			title="College Romance",
			author="Author Alpha",
			date="2025-05-10",
			word_count=500,
			path=story_path,
			content="This is a story about Jordi Santos.",
		)

		# Create NLP entries
		# Path inside NLP db starts with test_stories, but we normalize
		self._create_mock_nlp_db(
			filepath="test_stories/gay/college/story1.txt",
			text="Jordi Santos",
			label="PERSON",
		)

		# Filter by entity text & label
		res_ent = query_stories(entity_text="Jordi", entity_label="PERSON")
		self.assertEqual(len(res_ent), 1)
		self.assertEqual(res_ent[0]["title"], "College Romance")

		# Filter by non-existent entity
		res_ent_none = query_stories(entity_text="Bram Stoker", entity_label="PERSON")
		self.assertEqual(len(res_ent_none), 0)


class TestDashboardConfig(unittest.TestCase):
	"""Tests for src/storybuilder/dashboard/config.py functions."""

	def test_get_db_dir_default(self) -> None:
		from storybuilder.dashboard.config import get_db_dir

		result = get_db_dir()
		self.assertEqual(result, "stories/db")

	def test_get_nlp_db_path_default(self) -> None:
		from storybuilder.dashboard.config import get_nlp_db_path

		result = get_nlp_db_path()
		self.assertEqual(result, "stories/db/nlp_analysis.db")

	def test_get_meta_db_path_default(self) -> None:
		from storybuilder.dashboard.config import get_meta_db_path

		result = get_meta_db_path()
		self.assertEqual(result, "stories/db/dashboard_metadata.db")

	def test_get_db_dir_with_mock(self) -> None:
		import sys
		from storybuilder.dashboard.config import get_db_dir

		mock_module = type(sys)("dashboard")
		mock_module.DB_DIR = "custom/db/path"
		sys.modules["dashboard"] = mock_module

		try:
			result = get_db_dir()
			self.assertEqual(result, "custom/db/path")
		finally:
			del sys.modules["dashboard"]

	def test_get_nlp_db_path_with_mock(self) -> None:
		import sys
		from storybuilder.dashboard.config import get_nlp_db_path

		mock_module = type(sys)("dashboard")
		mock_module.NLP_DB_PATH = "custom/nlp.db"
		sys.modules["dashboard"] = mock_module

		try:
			result = get_nlp_db_path()
			self.assertEqual(result, "custom/nlp.db")
		finally:
			del sys.modules["dashboard"]

	def test_get_meta_db_path_with_mock(self) -> None:
		import sys
		from storybuilder.dashboard.config import get_meta_db_path

		mock_module = type(sys)("dashboard")
		mock_module.META_DB_PATH = "custom/meta.db"
		sys.modules["dashboard"] = mock_module

		try:
			result = get_meta_db_path()
			self.assertEqual(result, "custom/meta.db")
		finally:
			del sys.modules["dashboard"]

	def test_bracket_labels_constant(self) -> None:
		from storybuilder.dashboard.config import BRACKET_LABELS

		expected = [
			"Short (<1K)",
			"Medium-Short (1K-5K)",
			"Medium (5K-10K)",
			"Medium-Long (10K-20K)",
			"Long (20K-50K)",
			"Epic (>50K)",
		]
		self.assertEqual(BRACKET_LABELS, expected)

	def test_long_year_constant(self) -> None:
		from storybuilder.dashboard.config import LONG_YEAR

		self.assertEqual(LONG_YEAR, 4)


class TestDashboardDataFunctions(unittest.TestCase):
	"""Tests for src/storybuilder/dashboard/data.py functions."""

	def setUp(self) -> None:
		self.temp_dir = tempfile.mkdtemp()
		self.db_dir = os.path.join(self.temp_dir, "db")
		Path(self.db_dir).mkdir(exist_ok=True, parents=True)

		self.nlp_db_path = os.path.join(self.temp_dir, "nlp_analysis.db")
		self.meta_db_path = os.path.join(self.temp_dir, "dashboard_metadata.db")

		# Clear Streamlit cache to prevent state pollution
		import streamlit as st

		st.cache_data.clear()

		import storybuilder.downloader.db as sb_db

		sb_db.init_db(self.db_dir)

	def tearDown(self) -> None:
		shutil.rmtree(self.temp_dir, ignore_errors=True)

	def test_get_db_files_empty(self) -> None:
		import sys
		from unittest.mock import patch

		mock_module = type(sys)("dashboard")
		mock_module.DB_DIR = self.db_dir
		mock_module.NLP_DB_PATH = self.nlp_db_path
		mock_module.META_DB_PATH = self.meta_db_path
		sys.modules["dashboard"] = mock_module

		try:
			from storybuilder.dashboard.data import get_db_files

			result = get_db_files()
			self.assertEqual(result, [])
		finally:
			del sys.modules["dashboard"]

	def test_get_db_files_with_year_dbs(self) -> None:
		import sys
		from unittest.mock import patch

		mock_module = type(sys)("dashboard")
		mock_module.DB_DIR = self.db_dir
		mock_module.NLP_DB_PATH = self.nlp_db_path
		mock_module.META_DB_PATH = self.meta_db_path
		sys.modules["dashboard"] = mock_module

		try:
			Path(os.path.join(self.db_dir, "2025.db")).touch()
			Path(os.path.join(self.db_dir, "2024.db")).touch()
			Path(os.path.join(self.db_dir, "not_a_db.txt")).touch()

			from storybuilder.dashboard.data import get_db_files

			result = get_db_files()
			result_names = [f.name for f in result]
			self.assertEqual(result_names, ["2024.db", "2025.db"])
		finally:
			del sys.modules["dashboard"]

	def test_get_filter_options_with_data(self) -> None:
		import sys
		from unittest.mock import patch

		mock_module = type(sys)("dashboard")
		mock_module.DB_DIR = self.db_dir
		mock_module.NLP_DB_PATH = self.nlp_db_path
		mock_module.META_DB_PATH = self.meta_db_path
		sys.modules["dashboard"] = mock_module

		try:
			from storybuilder.dashboard.data import get_filter_options
			from storybuilder.downloader.db import insert_story

			insert_story(
				output_path="stories/gay/college/test1.txt",
				title="Test Story 1",
				author="Author A",
				story_date="2025-01-01",
				url="http://test",
				content="Test content",
			)
			insert_story(
				output_path="stories/gay/athletics/test2.txt",
				title="Test Story 2",
				author="Author B",
				story_date="2025-02-01",
				url="http://test",
				content="More test content",
			)

			categories, authors = get_filter_options()
			self.assertIn("college", categories)
			self.assertIn("athletics", categories)
			self.assertIn("Author A", authors)
			self.assertIn("Author B", authors)
		finally:
			del sys.modules["dashboard"]

	def test_load_archive_stats(self) -> None:
		import sys
		from unittest.mock import patch

		mock_module = type(sys)("dashboard")
		mock_module.DB_DIR = self.db_dir
		mock_module.NLP_DB_PATH = self.nlp_db_path
		mock_module.META_DB_PATH = self.meta_db_path
		sys.modules["dashboard"] = mock_module

		try:
			from storybuilder.dashboard.data import load_archive_stats
			from storybuilder.downloader.db import insert_story

			insert_story(
				output_path="stories/gay/college/test.txt",
				title="Test Story",
				author="Test Author",
				story_date="2025-06-15",
				url="http://test",
				content="Test content here",
			)

			df_years, df_cats, df_auths, df_words = load_archive_stats()

			self.assertFalse(df_years.empty)
			self.assertFalse(df_cats.empty)
			self.assertFalse(df_auths.empty)
		finally:
			del sys.modules["dashboard"]

	def test_get_story_by_path_exists(self) -> None:
		import sys

		mock_module = type(sys)("dashboard")
		mock_module.DB_DIR = self.db_dir
		mock_module.NLP_DB_PATH = self.nlp_db_path
		mock_module.META_DB_PATH = self.meta_db_path
		sys.modules["dashboard"] = mock_module

		try:
			from storybuilder.dashboard.data import get_story_by_path
			from storybuilder.downloader.db import insert_story

			insert_story(
				output_path="stories/gay/college/exist_test.txt",
				title="Existing Story",
				author="Test Author",
				story_date="2025-06-15",
				url="http://test",
				content="Story content here",
			)

			result = get_story_by_path("stories/gay/college/exist_test.txt")
			self.assertIsNotNone(result)
			self.assertEqual(result["title"], "Existing Story")
			self.assertEqual(result["author_name"], "Test Author")
		finally:
			del sys.modules["dashboard"]

	def test_get_story_by_path_not_found(self) -> None:
		import sys

		mock_module = type(sys)("dashboard")
		mock_module.DB_DIR = self.db_dir
		mock_module.NLP_DB_PATH = self.nlp_db_path
		mock_module.META_DB_PATH = self.meta_db_path
		sys.modules["dashboard"] = mock_module

		try:
			from storybuilder.dashboard.data import get_story_by_path

			result = get_story_by_path("nonexistent/story.txt")
			self.assertIsNone(result)
		finally:
			del sys.modules["dashboard"]

	def test_add_favorite_function(self) -> None:
		import sys

		mock_module = type(sys)("dashboard")
		mock_module.DB_DIR = self.db_dir
		mock_module.NLP_DB_PATH = self.nlp_db_path
		mock_module.META_DB_PATH = self.meta_db_path
		sys.modules["dashboard"] = mock_module

		try:
			from storybuilder.dashboard.data import add_favorite
			from storybuilder.dashboard.data import get_favorites
			from storybuilder.dashboard.data import remove_favorite

			success = add_favorite(
				"test/path.txt",
				"Test Title",
				"Test Author",
				"tag1,tag2",
				"Some notes",
			)
			self.assertTrue(success)

			favs = get_favorites()
			self.assertEqual(len(favs), 1)
			self.assertEqual(favs[0]["story_path"], "test/path.txt")
			self.assertEqual(favs[0]["title"], "Test Title")

			removed = remove_favorite("test/path.txt")
			self.assertTrue(removed)
			self.assertEqual(get_favorites(), [])
		finally:
			del sys.modules["dashboard"]

	def test_archive_stats_empty_db(self) -> None:
		"""Regression test for Fix #1: empty-DB stats guard should not crash."""
		import sys

		mock_module = type(sys)("dashboard")
		mock_module.DB_DIR = self.db_dir
		mock_module.NLP_DB_PATH = self.nlp_db_path
		mock_module.META_DB_PATH = self.meta_db_path
		sys.modules["dashboard"] = mock_module

		try:
			from storybuilder.dashboard.data import load_archive_stats

			# Call with no stories inserted → should return empty DataFrames
			df_years, df_cats, df_auths, df_words = load_archive_stats()

			# Verify all are empty
			self.assertTrue(df_years.empty, "df_years should be empty when no data is present")
			self.assertTrue(df_cats.empty, "df_cats should be empty when no data is present")
			self.assertTrue(df_auths.empty, "df_auths should be empty when no data is present")
			self.assertTrue(df_words.empty, "df_words should be empty when no data is present")
		finally:
			del sys.modules["dashboard"]

	def test_favorites_year_resolution_with_null_publication_date(self) -> None:
		"""Regression test for Fix #2: favorites year query via get_conn cursor."""
		import sys

		mock_module = type(sys)("dashboard")
		mock_module.DB_DIR = self.db_dir
		mock_module.NLP_DB_PATH = self.nlp_db_path
		mock_module.META_DB_PATH = self.meta_db_path
		sys.modules["dashboard"] = mock_module

		try:
			from storybuilder.downloader.db import get_conn
			from storybuilder.downloader.db import insert_story

			# Insert test stories with various publication_date formats (correct path format)
			insert_story(
				output_path="stories/gay/college/story1/part-1.txt",
				title="Story with valid year",
				author="Author One",
				story_date="2020-06-15",
				url="http://test1",
				content="Content 1",
			)

			insert_story(
				output_path="stories/gay/college/story2/part-1.txt",
				title="Story with no year",
				author="Author Two",
				story_date=None,  # pyrefly: ignore [bad-argument-type]
				url="http://test2",
				content="Content 2",
			)

			# Simulate the favorites query using get_conn with qmark parameters
			conn = get_conn()
			self.assertIsNotNone(conn, "get_conn should return a valid connection")

			cursor = conn.cursor()
			paths = ["stories/gay/college/story1/part-1.txt", "stories/gay/college/story2/part-1.txt"]
			placeholders = ",".join("?" for _ in paths)
			cursor.execute(
				f"SELECT path, publication_date FROM stories WHERE path IN ({placeholders})",
				paths,
			)
			rows = cursor.fetchall()

			# Verify we got results
			self.assertEqual(len(rows), 2, "Should retrieve both stories")

			import datetime

			current_year = datetime.datetime.now(datetime.timezone.utc).year

			# Check that we can extract years without crashing
			path_to_year = {}
			for row in rows:
				pub_date = row[1] if len(row) > 1 else None
				try:
					y = int(str(pub_date)[:4]) if pub_date and len(str(pub_date)) >= 4 else current_year
				except (ValueError, TypeError):
					y = current_year
				path_to_year[row[0]] = y

			self.assertEqual(path_to_year["stories/gay/college/story1/part-1.txt"], 2020, "Should extract year 2020")
			self.assertEqual(
				path_to_year["stories/gay/college/story2/part-1.txt"],
				current_year,
				f"Should default to {current_year} for None",
			)
		finally:
			del sys.modules["dashboard"]


if __name__ == "__main__":
	unittest.main()
