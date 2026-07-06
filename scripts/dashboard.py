import importlib
import sys
from pathlib import Path


# Ensure src layout package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Force reload dashboard submodules to ensure Streamlit server picks up file changes on refresh
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
from storybuilder.dashboard.config import init_session_state  # noqa: E402
from storybuilder.dashboard.config import inject_custom_css  # noqa: E402
from storybuilder.dashboard.config import setup_page  # noqa: E402

# Expose key data operations at module level to satisfy test imports
from storybuilder.dashboard.data import add_favorite  # noqa: E402, F401
from storybuilder.dashboard.data import get_db_files  # noqa: E402, F401
from storybuilder.dashboard.data import get_favorites  # noqa: E402, F401
from storybuilder.dashboard.data import get_story_by_path  # noqa: E402, F401
from storybuilder.dashboard.data import remove_favorite  # noqa: E402, F401

# Expose pages
from storybuilder.dashboard.pages.archive_stats import render_archive_stats  # noqa: E402
from storybuilder.dashboard.pages.favorites_tags import render_favorites_tags  # noqa: E402
from storybuilder.dashboard.pages.read_story import render_read_story  # noqa: E402
from storybuilder.dashboard.pages.search_explorer import render_search_explorer  # noqa: E402
from storybuilder.dashboard.ui.sidebar import render_sidebar  # noqa: E402


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
