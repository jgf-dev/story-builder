import datetime
import sqlite3
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
import pandas as pd
import streamlit as st
from storybuilder.dashboard.config import BRACKET_LABELS, LONG_YEAR, get_db_dir, get_meta_db_path, get_nlp_db_path
from storybuilder.downloader import db as storybuilder_db

logger: Logger


def get_db_files() -> list[Path]: ...


def get_meta_conn() -> sqlite3.Connection: ...


@st.cache_resource
def get_nlp_conn() -> sqlite3.Connection | None: ...


@st.cache_data
def get_filter_options() -> tuple[list[str], list[str]]: ...


@st.cache_data
def load_archive_stats() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]: ...


@dataclass
class StorySearchQuery:
    fts_query: str = ""
    category: str = "All"
    author: str = "All"
    year_range: tuple[int, int] | None = None
    entity_text: str = ""
    entity_label: str = "PERSON"
    limit: int = 100


def query_stories(params: StorySearchQuery | None = None, *, fts_query: str = "", category: str = "All", author: str = "All", year_range: tuple[int, int] | None = None, entity_text: str = "", entity_label: str = "PERSON", limit: int = 100) -> list[dict]: ...


def get_story_by_path(story_path: str, db_year: int | str | None = None) -> dict | None: ...


def add_favorite(story_path: str, title: str, author: str, tags: str | None, notes: str | None) -> bool: ...


def remove_favorite(story_path: str) -> bool: ...


def get_favorites() -> list[dict]: ...
