"""Deprecated: StorySearchQuery tests live in test_story_search_query.py.

This file was introduced redundantly; keep tests in the unittest-based module.
"""
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
