import importlib
import sys
from pathlib import Path

DB_DIR: Literal['stories/db'] = "stories/db"
NLP_DB_PATH: Literal['stories/db/nlp_analysis.db'] = "stories/db/nlp_analysis.db"
META_DB_PATH: Literal['stories/db/dashboard_metadata.db'] = "stories/db/dashboard_metadata.db"

from storybuilder.dashboard.config import init_session_state
from storybuilder.dashboard.config import inject_custom_css
from storybuilder.dashboard.config import setup_page
from storybuilder.dashboard.data import add_favorite
from storybuilder.dashboard.data import get_db_files
from storybuilder.dashboard.data import get_favorites
from storybuilder.dashboard.data import get_story_by_path
from storybuilder.dashboard.data import query_stories
from storybuilder.dashboard.data import remove_favorite
from storybuilder.dashboard.pages.archive_stats import render_archive_stats
from storybuilder.dashboard.pages.favorites_tags import render_favorites_tags
from storybuilder.dashboard.pages.read_story import render_read_story
from storybuilder.dashboard.pages.search_explorer import render_search_explorer
from storybuilder.dashboard.ui.sidebar import render_sidebar


def main() -> None: ...
