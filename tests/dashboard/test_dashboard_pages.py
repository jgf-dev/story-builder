import datetime
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

# Ensure src layout package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


class MockSessionState(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value


class TestDashboardPages(unittest.TestCase):
    """Unit tests for the modular dashboard page rendering modules."""

    # -- Config module tests --

    @patch("storybuilder.dashboard.config.os.environ", {})
    def test_config_paths_default(self) -> None:
        from storybuilder.dashboard.config import get_db_dir, get_nlp_db_path, get_meta_db_path
        self.assertEqual(get_db_dir(), "stories/db")
        self.assertEqual(get_nlp_db_path(), "stories/db/nlp_analysis.db")
        self.assertEqual(get_meta_db_path(), "stories/db/dashboard_metadata.db")

    @patch("storybuilder.dashboard.config.os.environ", {
        "STORYBUILDER_DB_DIR": "/env/db",
        "STORYBUILDER_NLP_DB_PATH": "/env/nlp.db",
        "STORYBUILDER_META_DB_PATH": "/env/meta.db"
    })
    def test_config_paths_env(self) -> None:
        from storybuilder.dashboard.config import get_db_dir, get_nlp_db_path, get_meta_db_path
        self.assertEqual(get_db_dir(), "/env/db")
        self.assertEqual(get_nlp_db_path(), "/env/nlp.db")
        self.assertEqual(get_meta_db_path(), "/env/meta.db")

    @patch("storybuilder.dashboard.config.st")
    def test_setup_page_and_css(self, mock_st) -> None:
        from storybuilder.dashboard.config import setup_page, inject_custom_css, init_session_state
        
        setup_page()
        mock_st.set_page_config.assert_called_once()
        
        inject_custom_css()
        mock_st.html.assert_called_once()
        
        mock_st.session_state = MockSessionState()
        init_session_state()
        self.assertIn("selected_story_path", mock_st.session_state)
        self.assertIsNone(mock_st.session_state.selected_story_path)

    # -- Sidebar module tests --

    @patch("storybuilder.dashboard.ui.sidebar.get_filter_options")
    @patch("storybuilder.dashboard.ui.sidebar.get_db_files")
    @patch("storybuilder.dashboard.ui.sidebar.st")
    def test_render_sidebar_multiple_db_files(self, mock_st, mock_get_db_files, mock_get_filter_options) -> None:
        from storybuilder.dashboard.ui.sidebar import render_sidebar
        
        mock_get_filter_options.return_value = (["college"], ["Author A"])
        mock_get_db_files.return_value = ["/path/to/2025.db", "/path/to/2026.db"]
        
        # Setup mock returns
        mock_st.sidebar.radio.return_value = "🔍 Search & Explorer"
        # 3 selectboxes: Category, Author, Entity Label
        mock_st.sidebar.selectbox.side_effect = ["college", "Author A", "PERSON"]
        mock_st.sidebar.slider.return_value = (2025, 2026)
        mock_st.sidebar.text_input.return_value = "Vampire"
        
        page, filters = render_sidebar()
        self.assertEqual(page, "🔍 Search & Explorer")
        self.assertEqual(filters["category"], "college")
        self.assertEqual(filters["author"], "Author A")
        self.assertEqual(filters["year_range"], (2025, 2026))
        self.assertEqual(filters["entity_label"], "PERSON")
        self.assertEqual(filters["entity_text"], "Vampire")

    @patch("storybuilder.dashboard.ui.sidebar.get_filter_options")
    @patch("storybuilder.dashboard.ui.sidebar.get_db_files")
    @patch("storybuilder.dashboard.ui.sidebar.st")
    def test_render_sidebar_single_db_file(self, mock_st, mock_get_db_files, mock_get_filter_options) -> None:
        from storybuilder.dashboard.ui.sidebar import render_sidebar
        
        mock_get_filter_options.return_value = ([], [])
        mock_get_db_files.return_value = ["/path/to/2025.db"]
        
        # Setup mock returns
        mock_st.sidebar.radio.return_value = "📖 Read Story"
        mock_st.sidebar.selectbox.side_effect = ["All", "All", "NORP"]
        mock_st.sidebar.text_input.return_value = ""
        
        page, filters = render_sidebar()
        self.assertEqual(page, "📖 Read Story")
        self.assertEqual(filters["year_range"], (2025, 2025))

    @patch("storybuilder.dashboard.ui.sidebar.get_filter_options")
    @patch("storybuilder.dashboard.ui.sidebar.get_db_files")
    @patch("storybuilder.dashboard.ui.sidebar.st")
    def test_render_sidebar_no_db_files(self, mock_st, mock_get_db_files, mock_get_filter_options) -> None:
        from storybuilder.dashboard.ui.sidebar import render_sidebar
        
        mock_get_filter_options.return_value = ([], [])
        mock_get_db_files.return_value = []
        
        # Setup mock returns
        mock_st.sidebar.radio.return_value = "📖 Read Story"
        mock_st.sidebar.selectbox.side_effect = ["All", "All", "NORP"]
        mock_st.sidebar.text_input.return_value = ""
        
        page, filters = render_sidebar()
        self.assertEqual(page, "📖 Read Story")
        current_year = datetime.datetime.now(datetime.UTC).year
        self.assertEqual(filters["year_range"], (1990, current_year))

    # -- Archive Stats page tests --

    @patch("storybuilder.dashboard.pages.archive_stats.load_archive_stats")
    @patch("storybuilder.dashboard.pages.archive_stats.st")
    def test_render_archive_stats_empty(self, mock_st, mock_load) -> None:
        from storybuilder.dashboard.pages.archive_stats import render_archive_stats
        
        # Empty dataframes
        mock_load.return_value = (pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
        
        render_archive_stats()
        mock_st.info.assert_called_once_with("No archive data available yet.")

    @patch("storybuilder.dashboard.pages.archive_stats.load_archive_stats")
    @patch("storybuilder.dashboard.pages.archive_stats.st")
    @patch("storybuilder.dashboard.pages.archive_stats.px")
    def test_render_archive_stats_populated(self, mock_px, mock_st, mock_load) -> None:
        from storybuilder.dashboard.pages.archive_stats import render_archive_stats
        
        df_years = pd.DataFrame({"Year": [2025], "Stories Count": [5], "Total Words": [5000]})
        df_cats = pd.DataFrame({"Category": ["college"], "Count": [5]})
        df_auths = pd.DataFrame({"Author": ["Author A"], "Count": [5]})
        df_words = pd.DataFrame({"Bracket": ["Short (<1K)"], "Stories": [5]})
        mock_load.return_value = (df_years, df_cats, df_auths, df_words)
        
        # st.columns(3) for metrics, and st.columns(2) for charts
        mock_metric_cols = [MagicMock(), MagicMock(), MagicMock()]
        mock_chart_cols = [MagicMock(), MagicMock()]
        mock_st.columns.side_effect = [mock_metric_cols, mock_chart_cols]
        
        mock_fig = MagicMock()
        mock_px.line.return_value = mock_fig
        mock_px.bar.return_value = mock_fig
        
        render_archive_stats()
        
        # Verify metric calls
        mock_metric_cols[0].metric.assert_called_once_with("Total Stories", "5")
        mock_metric_cols[1].metric.assert_called_once_with("Total Archive Words", "5,000")
        
        # Verify plotly_chart is called
        self.assertEqual(mock_st.plotly_chart.call_count, 4)

    # -- Favorites & Tags page tests --

    @patch("storybuilder.dashboard.pages.favorites_tags.get_favorites")
    @patch("storybuilder.dashboard.pages.favorites_tags.st")
    def test_render_favorites_empty(self, mock_st, mock_get_favorites) -> None:
        from storybuilder.dashboard.pages.favorites_tags import render_favorites_tags
        mock_get_favorites.return_value = []
        
        render_favorites_tags()
        mock_st.info.assert_called_once()

    @patch("storybuilder.dashboard.pages.favorites_tags.get_favorites_publication_years")
    @patch("storybuilder.dashboard.pages.favorites_tags.get_favorites")
    @patch("storybuilder.dashboard.pages.favorites_tags.st")
    def test_render_favorites_populated_tag_filter_all(self, mock_st, mock_get_favorites, mock_get_years) -> None:
        from storybuilder.dashboard.pages.favorites_tags import render_favorites_tags
        
        favorites = [
            {"story_path": "path1.txt", "title": "Title 1", "author": "Author 1", "tags": "tag1,tag2", "notes": "Notes 1"},
            {"story_path": "path2.txt", "title": "Title 2", "author": "Author 2", "tags": "tag2", "notes": "Notes 2"}
        ]
        mock_get_favorites.return_value = favorites
        mock_get_years.return_value = {"path1.txt": 2025, "path2.txt": 2026}
        
        mock_st.selectbox.return_value = "All"
        
        # Mock two columns call (one per card)
        col1 = MagicMock()
        col2 = MagicMock()
        mock_st.columns.return_value = [col1, col2]
        
        # Setup session state
        mock_st.session_state = MockSessionState()
        mock_st.query_params = {}
        
        # Mock st.button to click "Read" for path1
        mock_st.button.side_effect = lambda label, key=None: key == "read_fav_path1.txt"
        
        render_favorites_tags()
        
        self.assertEqual(mock_st.session_state.selected_story_path, "path1.txt")
        self.assertEqual(mock_st.session_state.selected_story_year, 2025)
        mock_st.rerun.assert_called_once()

    @patch("storybuilder.dashboard.pages.favorites_tags.get_favorites_publication_years")
    @patch("storybuilder.dashboard.pages.favorites_tags.get_favorites")
    @patch("storybuilder.dashboard.pages.favorites_tags.st")
    def test_render_favorites_populated_tag_filter_specific(self, mock_st, mock_get_favorites, mock_get_years) -> None:
        from storybuilder.dashboard.pages.favorites_tags import render_favorites_tags
        
        favorites = [
            {"story_path": "path1.txt", "title": "Title 1", "author": "Author 1", "tags": "tag1,tag2", "notes": "Notes 1"},
            {"story_path": "path2.txt", "title": "Title 2", "author": "Author 2", "tags": None, "notes": "Notes 2"},
            {"story_path": "path3.txt", "title": "Title 3", "author": "Author 3", "tags": "tag3", "notes": "Notes 3"}
        ]
        mock_get_favorites.return_value = favorites
        mock_get_years.return_value = {"path1.txt": 2025, "path3.txt": 2026}
        
        # Select "tag1"
        mock_st.selectbox.return_value = "tag1"
        
        col1 = MagicMock()
        col2 = MagicMock()
        mock_st.columns.return_value = [col1, col2]
        mock_st.button.return_value = False
        
        render_favorites_tags()
        
        # Verify markdown was called for Title 1 but NOT Title 3
        markdown_calls = [call[0][0] for call in mock_st.markdown.call_args_list]
        self.assertTrue(any("Title 1" in c for c in markdown_calls))
        self.assertFalse(any("Title 3" in c for c in markdown_calls))

    # -- Read Story page tests --

    @patch("storybuilder.dashboard.pages.read_story.st")
    def test_render_read_story_no_selected(self, mock_st) -> None:
        from storybuilder.dashboard.pages.read_story import render_read_story
        
        # No selected story
        mock_st.session_state = MockSessionState(selected_story_path=None)
        
        render_read_story()
        mock_st.warning.assert_called_once_with("No story selected. Please go to 'Search & Explorer' first to pick a story.")

    @patch("storybuilder.dashboard.pages.read_story.get_story_by_path")
    @patch("storybuilder.dashboard.pages.read_story.st")
    def test_render_read_story_load_error(self, mock_st, mock_get_story) -> None:
        from storybuilder.dashboard.pages.read_story import render_read_story
        
        mock_st.session_state = MockSessionState(selected_story_path="path.txt", selected_story_year=2025)
        mock_get_story.return_value = None
        
        render_read_story()
        mock_st.error.assert_called_once_with("Error loading story contents.")

    @patch("storybuilder.dashboard.pages.read_story.remove_favorite")
    @patch("storybuilder.dashboard.pages.read_story.add_favorite")
    @patch("storybuilder.dashboard.pages.read_story.get_favorites")
    @patch("storybuilder.dashboard.pages.read_story.get_story_by_path")
    @patch("storybuilder.dashboard.pages.read_story.st")
    def test_render_read_story_is_favorite_update_and_remove(self, mock_st, mock_get_story, mock_get_favorites, mock_add_favorite, mock_remove_favorite) -> None:
        from storybuilder.dashboard.pages.read_story import render_read_story
        
        mock_st.session_state = MockSessionState(selected_story_path="path1.txt", selected_story_year="2025")
        story = {
            "path": "path1.txt", "title": "Story Title", "author_name": "Author A",
            "category": "college", "publication_date": "2025-01-01", "url": "http://url",
            "content": "Story content goes here.", "story_slug": "story-title"
        }
        mock_get_story.return_value = story
        
        favorites = [{"story_path": "path1.txt", "title": "Story Title", "author": "Author A", "tags": "fav_tag", "notes": "notes"}]
        mock_get_favorites.return_value = favorites
        
        # Columns setup
        col_title = MagicMock()
        col_actions = MagicMock()
        mock_st.columns.return_value = [col_title, col_actions]
        
        # Setup inputs inside expander
        mock_st.text_input.return_value = "new_tag"
        mock_st.text_area.return_value = "new_notes"
        
        # First rendering where Update Info button is clicked
        mock_st.button.side_effect = lambda label: label == "Update Info"
        
        render_read_story()
        
        mock_add_favorite.assert_called_once_with("path1.txt", "Story Title", "Author A", "new_tag", "new_notes")
        
        # Reset and mock Remove from Favorites click
        mock_add_favorite.reset_mock()
        mock_st.button.side_effect = lambda label: label == "Remove from Favorites"
        
        render_read_story()
        mock_remove_favorite.assert_called_once_with("path1.txt")
        mock_st.rerun.assert_called_once()

    @patch("storybuilder.dashboard.pages.read_story.add_favorite")
    @patch("storybuilder.dashboard.pages.read_story.get_favorites")
    @patch("storybuilder.dashboard.pages.read_story.get_story_by_path")
    @patch("storybuilder.dashboard.pages.read_story.st")
    def test_render_read_story_not_favorite_add(self, mock_st, mock_get_story, mock_get_favorites, mock_add_favorite) -> None:
        from storybuilder.dashboard.pages.read_story import render_read_story
        
        mock_st.session_state = MockSessionState(selected_story_path="path1.txt", selected_story_year="2025")
        story = {
            "path": "path1.txt", "title": "Story Title", "author_name": "Author A",
            "category": "college", "publication_date": "2025-01-01", "url": "http://url",
            "content": "Story content goes here.", "story_slug": "story-title"
        }
        mock_get_story.return_value = story
        mock_get_favorites.return_value = []
        
        # Columns setup
        col_title = MagicMock()
        col_actions = MagicMock()
        mock_st.columns.return_value = [col_title, col_actions]
        
        # Setup inputs inside expander
        mock_st.text_input.return_value = "favorite"
        mock_st.text_area.return_value = "new notes"
        
        mock_st.button.side_effect = lambda label: label == "Add to Favorites"
        
        render_read_story()
        
        mock_add_favorite.assert_called_once_with("path1.txt", "Story Title", "Author A", "favorite", "new notes")
        mock_st.rerun.assert_called_once()

    # -- Search Explorer page tests --

    @patch("storybuilder.dashboard.pages.search_explorer.query_stories")
    @patch("storybuilder.dashboard.pages.search_explorer.st")
    def test_render_search_explorer_no_results(self, mock_st, mock_query) -> None:
        from storybuilder.dashboard.pages.search_explorer import render_search_explorer
        
        filters = {"category": "college", "author": "All", "year_range": (2025, 2026), "entity_label": "PERSON", "entity_text": ""}
        mock_st.text_input.return_value = "search term"
        mock_query.return_value = []
        
        render_search_explorer(filters)
        
        mock_st.subheader.assert_called_once_with("Found 0 Result(s)")

    @patch("storybuilder.dashboard.pages.search_explorer.query_stories")
    @patch("storybuilder.dashboard.pages.search_explorer.st")
    def test_render_search_explorer_results_and_read(self, mock_st, mock_query) -> None:
        from storybuilder.dashboard.pages.search_explorer import render_search_explorer
        
        filters = {"category": "All", "author": "All", "year_range": (2025, 2026), "entity_label": "PERSON", "entity_text": ""}
        mock_st.text_input.return_value = ""
        
        results = [
            {
                "path": "path1.txt", "db_year": 2025, "title": "Title 1", "author_name": "Author 1",
                "category": "college", "publication_date": "2025-01-01", "word_count": 1000,
                "snippet": "___HIGHLIGHT_START___match___HIGHLIGHT_END___ in text"
            }
        ]
        mock_query.return_value = results
        
        col1 = MagicMock()
        col2 = MagicMock()
        mock_st.columns.return_value = [col1, col2]
        
        mock_st.session_state = MockSessionState()
        mock_st.query_params = {}
        
        # Click read button
        mock_st.button.return_value = True
        
        render_search_explorer(filters)
        
        self.assertEqual(mock_st.session_state.selected_story_path, "path1.txt")
        self.assertEqual(mock_st.session_state.selected_story_year, 2025)
        self.assertEqual(mock_st.session_state["nav_page"], "📖 Read Story")
        mock_st.rerun.assert_called_once()


if __name__ == "__main__":
    unittest.main()
