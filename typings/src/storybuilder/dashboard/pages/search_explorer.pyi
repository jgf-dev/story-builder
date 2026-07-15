import html
import streamlit as st
from storybuilder.dashboard.data import StorySearchQuery
from storybuilder.dashboard.data import query_stories


def render_search_explorer(filters: dict) -> None: ...
