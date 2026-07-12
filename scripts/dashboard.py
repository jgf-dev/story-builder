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

    for res in search_results:
        # Create a container for the card styling
        safe_title = html.escape(res["title"] or "")
        safe_author = html.escape(res["author_name"] or "Unknown")
        safe_category = html.escape(res["category"] or "")
        safe_pub_date = html.escape(str(res["publication_date"] or "Unknown"))
        card_html = f"""
        <div class="story-card">
            <h4>{safe_title}</h4>
            <p style='color: #a9b6d8; font-size: 0.95rem; margin-bottom: 8px;'>
                <b>Author:</b> {safe_author} |
                <b>Category:</b> {safe_category} |
                <b>Published:</b> {safe_pub_date} |
                <b>Words:</b> {res["word_count"]:,}
            </p>
        """

        # Display highlighted snippets if any
        if res.get("snippet"):
            # Escape the snippet first, then replace the placeholder highlight markers with actual HTML span tags
            snippet_escaped = html.escape(res["snippet"])
            snippet_cleaned = snippet_escaped.replace(
                "___HIGHLIGHT_START___", "<span class='highlight'>",
            ).replace("___HIGHLIGHT_END___", "</span>")
            card_html += f"<p style='color: #cbd5e1; font-style: italic; font-size: 0.92rem; background: rgba(0, 0, 0, 0.2); padding: 8px; border-radius: 6px;'>... {snippet_cleaned} ...</p>"

        card_html += "</div>"
        st.markdown(card_html, unsafe_allow_html=True)

        # Action buttons on the card
        col1, col2 = st.columns([1, 8])
        with col1:
            if st.button("Read", key=f"read_{res['path']}_{res['db_year']}"):
                st.session_state.selected_story_path = res["path"]
                st.session_state.selected_story_year = res["db_year"]
                # Programmatically update radio key by modifying query params or session state navigation
                st.query_params["nav_page"] = "📖 Read Story"
                st.rerun()
        st.write("")
