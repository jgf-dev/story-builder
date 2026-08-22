from _typeshed import Incomplete

import argparse
import sqlite3
from pathlib import Path
from sqlite3 import Connection
import pandas as pd
import plotly.graph_objects as go
from pandas.core.frame import DataFrame
from plotly.graph_objs._figure import Figure


def fetch_story(conn: Connection, story_query: Incomplete = None) -> tuple[int, Any] | tuple[None, None]: ...


def get_overall_sentiment(conn: Connection, story_id: int, window: Incomplete) -> DataFrame: ...


def get_top_characters(conn: Connection, story_id: int, limit: Incomplete = 5) -> list[Any]: ...


def get_character_sentiment(conn: Connection, story_id: int, char: Incomplete, df_sentences: DataFrame, window: Incomplete) -> DataFrame: ...


def plot_narrative_arcs(story_dir: Incomplete, df_sentences: DataFrame, char_arcs: Incomplete) -> tuple[Figure, str]: ...


def main() -> None: ...
