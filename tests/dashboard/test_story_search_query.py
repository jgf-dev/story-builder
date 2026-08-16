"""Tests for the StorySearchQuery dataclass in storybuilder.dashboard.data."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from storybuilder.dashboard.data import StorySearchQuery


class TestStorySearchQueryDefaults(unittest.TestCase):
    """Tests for default initialization of StorySearchQuery."""

    def test_default_fts_query(self) -> None:
        q = StorySearchQuery()
        self.assertEqual(q.fts_query, "")

    def test_default_category(self) -> None:
        q = StorySearchQuery()
        self.assertEqual(q.category, "All")

    def test_default_author(self) -> None:
        q = StorySearchQuery()
        self.assertEqual(q.author, "All")

    def test_default_year_range(self) -> None:
        q = StorySearchQuery()
        self.assertIsNone(q.year_range)

    def test_default_entity_text(self) -> None:
        q = StorySearchQuery()
        self.assertEqual(q.entity_text, "")

    def test_default_entity_label(self) -> None:
        q = StorySearchQuery()
        self.assertEqual(q.entity_label, "PERSON")

    def test_default_limit(self) -> None:
        q = StorySearchQuery()
        self.assertEqual(q.limit, 100)


class TestStorySearchQueryCustom(unittest.TestCase):
    """Tests for custom initialization of StorySearchQuery."""

    def test_custom_fts_query(self) -> None:
        q = StorySearchQuery(fts_query="adventure")
        self.assertEqual(q.fts_query, "adventure")

    def test_custom_category(self) -> None:
        q = StorySearchQuery(category="gay")
        self.assertEqual(q.category, "gay")

    def test_custom_author(self) -> None:
        q = StorySearchQuery(author="Jane Doe")
        self.assertEqual(q.author, "Jane Doe")

    def test_custom_year_range(self) -> None:
        q = StorySearchQuery(year_range=(2000, 2020))
        self.assertEqual(q.year_range, (2000, 2020))

    def test_custom_entity_text(self) -> None:
        q = StorySearchQuery(entity_text="Alex")
        self.assertEqual(q.entity_text, "Alex")

    def test_custom_entity_label(self) -> None:
        q = StorySearchQuery(entity_label="ORG")
        self.assertEqual(q.entity_label, "ORG")

    def test_custom_limit(self) -> None:
        q = StorySearchQuery(limit=50)
        self.assertEqual(q.limit, 50)

    def test_all_custom_fields(self) -> None:
        q = StorySearchQuery(
            fts_query="mystery",
            category="lesbian",
            author="Author Name",
            year_range=(1995, 2005),
            entity_text="Sam",
            entity_label="PERSON",
            limit=25,
        )
        self.assertEqual(q.fts_query, "mystery")
        self.assertEqual(q.category, "lesbian")
        self.assertEqual(q.author, "Author Name")
        self.assertEqual(q.year_range, (1995, 2005))
        self.assertEqual(q.entity_text, "Sam")
        self.assertEqual(q.entity_label, "PERSON")
        self.assertEqual(q.limit, 25)


if __name__ == "__main__":
    unittest.main()
