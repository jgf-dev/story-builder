import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


class TestDashboardStreamlitUI(unittest.TestCase):
    """Tests for Streamlit dashboard UI - simpler integration tests."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.db_dir = os.path.join(self.temp_dir, "db")
        Path(self.db_dir).mkdir(exist_ok=True, parents=True)

        self.nlp_db_path = os.path.join(self.temp_dir, "nlp_analysis.db")
        self.meta_db_path = os.path.join(self.temp_dir, "dashboard_metadata.db")

        import storybuilder.downloader.db as sb_db
        sb_db.init_db(self.db_dir)

        sb_db.insert_story(
            output_path="stories/gay/college/test1.txt",
            title="Test Story 1",
            author="Author A",
            story_date="2025-01-01",
            url="http://test",
            content="Test content",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_dashboard_module_imports(self) -> None:
        """Test that all dashboard modules can be imported."""
        from storybuilder.dashboard import config
        from storybuilder.dashboard import data
        from storybuilder.dashboard.pages import archive_stats
        from storybuilder.dashboard.pages import favorites_tags
        from storybuilder.dashboard.pages import read_story
        from storybuilder.dashboard.pages import search_explorer
        from storybuilder.dashboard.ui import sidebar

        self.assertTrue(hasattr(config, "get_db_dir"))
        self.assertTrue(hasattr(data, "query_stories"))
        self.assertTrue(hasattr(sidebar, "render_sidebar"))

    def test_dashboard_pages_have_render_functions(self) -> None:
        """Test that all dashboard pages have render functions."""
        from storybuilder.dashboard.pages import archive_stats
        from storybuilder.dashboard.pages import favorites_tags
        from storybuilder.dashboard.pages import read_story
        from storybuilder.dashboard.pages import search_explorer

        self.assertTrue(callable(archive_stats.render_archive_stats))
        self.assertTrue(callable(favorites_tags.render_favorites_tags))
        self.assertTrue(callable(read_story.render_read_story))
        self.assertTrue(callable(search_explorer.render_search_explorer))

    def test_config_constants(self) -> None:
        """Test dashboard config constants."""
        from storybuilder.dashboard.config import BRACKET_LABELS
        from storybuilder.dashboard.config import LONG_YEAR

        self.assertEqual(LONG_YEAR, 4)
        self.assertEqual(len(BRACKET_LABELS), 6)
        self.assertIn("Short (<1K)", BRACKET_LABELS)
        self.assertIn("Epic (>50K)", BRACKET_LABELS)

    def test_data_functions_available(self) -> None:
        """Test that data module exposes expected functions."""
        from storybuilder.dashboard import data

        expected_funcs = [
            "get_db_files",
            "get_filter_options",
            "query_stories",
            "get_story_by_path",
            "add_favorite",
            "remove_favorite",
            "get_favorites",
            "load_archive_stats",
        ]

        for func_name in expected_funcs:
            self.assertTrue(
                hasattr(data, func_name),
                f"data module should have {func_name}"
            )

    def test_launcher_script_imports_work(self) -> None:
        """Test that scripts/dashboard.py can import all needed modules."""
        import sys
        from importlib.util import module_from_spec
        from importlib.util import spec_from_file_location
        from pathlib import Path

        script_path = Path("scripts/dashboard.py")
        spec = spec_from_file_location("dashboard_launcher", script_path)
        if spec is None or spec.loader is None:
            self.fail("Could not load spec or loader for scripts/dashboard.py")
            return

        module = module_from_spec(spec)

        try:
            spec.loader.exec_module(module)

            self.assertTrue(hasattr(module, "main"))
            self.assertTrue(hasattr(module, "render_sidebar"))
            self.assertTrue(callable(module.main))
        except Exception as e:
            self.fail(f"Failed to load dashboard launcher: {e}")


if __name__ == "__main__":
    unittest.main()