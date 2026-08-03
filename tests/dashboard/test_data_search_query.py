# ruff: ignore[implicit-namespace-package]
"""Tests for StorySearchQuery in storybuilder.dashboard.data."""

from storybuilder.dashboard.data import StorySearchQuery


def test_story_search_query_default() -> None:
    """Test default initialization of StorySearchQuery."""
    query = StorySearchQuery()
    # ruff: ignore[assert, compare-to-empty-string]
    assert query.fts_query == ""
    # ruff: ignore[assert]
    assert query.category == "All"
    # ruff: ignore[assert]
    assert query.author == "All"
    # ruff: ignore[assert]
    assert query.year_range is None
    # ruff: ignore[assert, compare-to-empty-string]
    assert query.entity_text == ""
    # ruff: ignore[assert]
    assert query.entity_label == "PERSON"
    # ruff: ignore[assert, magic-value-comparison]
    assert query.limit == 100


def test_story_search_query_custom() -> None:
    """Test custom initialization of StorySearchQuery."""
    query = StorySearchQuery(
        fts_query="test",
        category="Sci-Fi",
        author="John Doe",
        year_range=(2020, 2025),
        entity_text="Jane",
        entity_label="ORG",
        limit=50,
    )
    # ruff: ignore[assert]
    assert query.fts_query == "test"
    # ruff: ignore[assert]
    assert query.category == "Sci-Fi"
    # ruff: ignore[assert]
    assert query.author == "John Doe"
    # ruff: ignore[assert]
    assert query.year_range == (2020, 2025)
    # ruff: ignore[assert]
    assert query.entity_text == "Jane"
    # ruff: ignore[assert]
    assert query.entity_label == "ORG"
    # ruff: ignore[assert, magic-value-comparison]
    assert query.limit == 50
