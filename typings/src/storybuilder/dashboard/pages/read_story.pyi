import textwrap
import streamlit as st
from storybuilder.dashboard.data import add_favorite, get_favorites, get_story_by_path, remove_favorite


def render_read_story() -> None: ...
