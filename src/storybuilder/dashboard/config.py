import os
import sys
from pathlib import Path

import streamlit as st


# Shared Constants
LONG_YEAR = 4
BRACKET_LABELS = [
	"Short (<1K)",
	"Medium-Short (1K-5K)",
	"Medium (5K-10K)",
	"Medium-Long (10K-20K)",
	"Long (20K-50K)",
	"Epic (>50K)",
]


def get_db_dir() -> str:
	"""Retrieve the DB directory path, dynamically checking for environment variables or active testing mocks."""
	if "STORYBUILDER_DB_DIR" in os.environ:
		return os.environ["STORYBUILDER_DB_DIR"]
	for mod_name in ("__main__", "dashboard"):
		if mod_name in sys.modules:
			val = getattr(sys.modules[mod_name], "DB_DIR", None)
			if val is not None:
				return val
	return "stories/db"


def get_nlp_db_path() -> str:
	"""Retrieve the NLP DB path, dynamically checking for environment variables or active testing mocks."""
	if "STORYBUILDER_NLP_DB_PATH" in os.environ:
		return os.environ["STORYBUILDER_NLP_DB_PATH"]
	for mod_name in ("__main__", "dashboard"):
		if mod_name in sys.modules:
			val = getattr(sys.modules[mod_name], "NLP_DB_PATH", None)
			if val is not None:
				return val
	return str(Path(get_db_dir()) / "nlp_analysis.db")


def get_meta_db_path() -> str:
	"""Retrieve the metadata DB path, dynamically checking for environment variables or active testing mocks."""
	if "STORYBUILDER_META_DB_PATH" in os.environ:
		return os.environ["STORYBUILDER_META_DB_PATH"]
	for mod_name in ("__main__", "dashboard"):
		if mod_name in sys.modules:
			val = getattr(sys.modules[mod_name], "META_DB_PATH", None)
			if val is not None:
				return val
	return str(Path(get_db_dir()) / "dashboard_metadata.db")


def setup_page() -> None:
	"""Configure basic page properties."""
	st.set_page_config(
		page_title="StoryBuilder Workspace Dashboard",
		page_icon="📚",
		layout="wide",
		initial_sidebar_state="expanded",
	)


def inject_custom_css() -> None:
	"""Inject styling override for premium design."""
	st.html(
		"""
        <style>
            /* Main background and container styling */
            .reportview-container {
                background: #0b1020;
            }

            /* Heading styles */
            h1, h2, h3 {
                font-family: 'Outfit', 'Inter', sans-serif;
                font-weight: 700;
                color: #e8eefc;
            }

            /* Card styling */
            .story-card {
                background-color: rgba(22, 34, 64, 0.6);
                border: 1px solid rgba(148, 163, 184, 0.15);
                border-radius: 12px;
                padding: 18px;
                margin-bottom: 12px;
                transition: all 0.2s ease-in-out;
            }
            .story-card:hover {
                border-color: rgba(125, 211, 252, 0.4);
                transform: translateY(-2px);
                background-color: rgba(22, 34, 64, 0.85);
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
            }

            /* Snippet highlight styling */
            .highlight {
                background-color: rgba(251, 191, 36, 0.25);
                color: #fbbf24;
                padding: 2px 4px;
                border-radius: 4px;
                font-weight: bold;
            }

            /* Sidebar styling custom overrides */
            .css-1d391kg {
                background-color: #09101f;
            }
        </style>
        """,
	)


def init_session_state() -> None:
	"""Initialize shared routing states in session state."""
	if "selected_story_path" not in st.session_state:
		st.session_state.selected_story_path = None
	if "selected_story_year" not in st.session_state:
		st.session_state.selected_story_year = None
