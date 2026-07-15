import streamlit as st
from storybuilder.dashboard.data import add_favorite
from storybuilder.dashboard.data import get_favorites
from storybuilder.dashboard.data import get_story_by_path
from storybuilder.dashboard.data import remove_favorite


def render_read_story() -> None: ...
