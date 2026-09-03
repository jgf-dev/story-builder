# ruff: noqa: E402
import importlib
import os
import sys
from pathlib import Path


# Ensure src layout package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Force reload dashboard submodules only in developer mode to preserve Streamlit caching
if os.getenv("DASHBOARD_DEV_MODE", "false").lower() == "true":
	if "storybuilder.dashboard.config" in sys.modules:
		importlib.reload(sys.modules["storybuilder.dashboard.config"])
	if "storybuilder.dashboard.data" in sys.modules:
		importlib.reload(sys.modules["storybuilder.dashboard.data"])
	if "storybuilder.dashboard.ui.sidebar" in sys.modules:
		importlib.reload(sys.modules["storybuilder.dashboard.ui.sidebar"])
	if "storybuilder.dashboard.pages.search_explorer" in sys.modules:
		importlib.reload(sys.modules["storybuilder.dashboard.pages.search_explorer"])
	if "storybuilder.dashboard.pages.read_story" in sys.modules:
		importlib.reload(sys.modules["storybuilder.dashboard.pages.read_story"])
	if "storybuilder.dashboard.pages.favorites_tags" in sys.modules:
		importlib.reload(sys.modules["storybuilder.dashboard.pages.favorites_tags"])
	if "storybuilder.dashboard.pages.archive_stats" in sys.modules:
		importlib.reload(sys.modules["storybuilder.dashboard.pages.archive_stats"])

# Global variables for testing patches (keep these exactly as in original to satisfy test patching)
DB_DIR = "stories/db"
NLP_DB_PATH = "stories/db/nlp_analysis.db"
META_DB_PATH = "stories/db/dashboard_metadata.db"

# Rerouting rendering to modular components
from storybuilder.dashboard.config import init_session_state
from storybuilder.dashboard.config import inject_custom_css
from storybuilder.dashboard.config import setup_page

# Expose key data operations at module level to satisfy test imports
from storybuilder.dashboard.data import add_favorite  # noqa: F401
from storybuilder.dashboard.data import get_db_files  # noqa: F401
from storybuilder.dashboard.data import get_favorites  # noqa: F401
from storybuilder.dashboard.data import get_story_by_path  # noqa: F401
from storybuilder.dashboard.data import query_stories  # noqa: F401
from storybuilder.dashboard.data import remove_favorite  # noqa: F401

# Expose pages
from storybuilder.dashboard.pages.archive_stats import render_archive_stats
from storybuilder.dashboard.pages.favorites_tags import render_favorites_tags
from storybuilder.dashboard.pages.read_story import render_read_story
from storybuilder.dashboard.pages.search_explorer import render_search_explorer
from storybuilder.dashboard.ui.sidebar import render_sidebar


def main() -> None:
	# Setup page configurations as the first Streamlit instruction
	setup_page()
	inject_custom_css()
	init_session_state()

	# Render sidebar and retrieve routing & filter inputs
	page, filters = render_sidebar()

	# Route and render pages
	if page == "🔍 Search & Explorer":
		render_search_explorer(filters)
	elif page == "📖 Read Story":
		render_read_story()
	elif page == "⭐ Favorites & Tags":
		render_favorites_tags()
	elif page == "📊 Archive Stats":
		render_archive_stats()


if __name__ == "__main__":
	main()
