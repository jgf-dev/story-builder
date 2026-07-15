import sys
import streamlit as st

LONG_YEAR: Literal[4] = 4
BRACKET_LABELS: list[str]


def get_db_dir() -> str: ...


def get_nlp_db_path() -> str: ...


def get_meta_db_path() -> str: ...


def setup_page() -> None: ...


def inject_custom_css() -> None: ...


def init_session_state() -> None: ...
