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


class TestDashboard(unittest.TestCase):
    """Tests for the main dashboard logic in scripts/dashboard.py."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_dir = os.path.join(self.temp_dir, "db")
        os.makedirs(self.db_dir, exist_ok=True)

        self.nlp_db_path = os.path.join(self.temp_dir, "nlp_analysis.db")
        self.meta_db_path = os.path.join(self.temp_dir, "dashboard_metadata.db")

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

    def tearDown(self):
        self.patch_dir.stop()
        self.patch_nlp.stop()
        self.patch_meta.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_mock_partition(
        self, year, category, title, author, date, word_count, path, content
    ):
        from storybuilder.downloader import db as sb_db
        from sqlmodel import Session, select
        
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

    def _create_mock_nlp_db(self, filepath, text, label):
        conn = sqlite3.connect(self.nlp_db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT UNIQUE,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
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
            """
        )
        conn.execute(
            "INSERT OR REPLACE INTO stories (filepath) VALUES (?)", (filepath,)
        )
        story_id = conn.execute(
            "SELECT id FROM stories WHERE filepath = ?", (filepath,)
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO entities (story_id, text, label, frequency) VALUES (?, ?, ?, 1)",
            (story_id, text, label),
        )
        conn.commit()
        conn.close()

    def test_get_db_files(self):
        from dashboard import get_db_files

        self.assertEqual(get_db_files(), [])

        # Create mock db files
        open(os.path.join(self.db_dir, "2025.db"), "w").close()
        open(os.path.join(self.db_dir, "2026.db"), "w").close()

        files = [os.path.basename(f) for f in get_db_files()]
        self.assertEqual(files, ["2025.db", "2026.db"])

    def test_favorites_crud(self):
        from dashboard import add_favorite, get_favorites, remove_favorite

        # Initial empty
        self.assertEqual(get_favorites(), [])

        # Add favorite
        success = add_favorite(
            "test_path.txt", "Test Story", "Test Author", "tag1,tag2", "Some notes"
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

    def test_query_stories_metadata(self):
        from dashboard import query_stories

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

    def test_query_stories_fts(self):
        from dashboard import query_stories

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

    def test_query_stories_with_entities(self):
        from dashboard import query_stories

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


if __name__ == "__main__":
    unittest.main()
