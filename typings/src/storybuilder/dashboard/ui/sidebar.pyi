from pathlib import Path
import streamlit as st
from storybuilder.dashboard.data import get_db_files
from storybuilder.dashboard.data import get_filter_options


def render_sidebar() -> tuple[str, dict]: ...
