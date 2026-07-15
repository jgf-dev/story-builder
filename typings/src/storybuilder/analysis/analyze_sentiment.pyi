from _typeshed import Incomplete

from sqlite3 import Cursor
from sqlite3 import Connection
from spacy.language import Language
from argparse import Namespace
import argparse
import re
import sqlite3
from collections import defaultdict
from pathlib import Path
import spacy
from thinc.api import require_gpu
from thinc.api import set_gpu_allocator
from tqdm import tqdm
from transformers import pipeline

DB_PATH: Literal['sentiment_analysis.db'] = "sentiment_analysis.db"
ALLOWED_LABELS: set[str]


def init_db(db_path: Incomplete) -> Connection: ...


def get_sentiment_value(result: Incomplete) -> Incomplete: ...


def extract_chapter_number(filename: Incomplete) -> int: ...


def parse_args() -> Namespace: ...


def find_multi_chapter_stories(stories_dir: Incomplete, subcategory: Incomplete = None) -> Incomplete: ...


def load_models(spacy_model_name: Incomplete, sentiment_model_name: Incomplete, use_gpu: Incomplete) -> Incomplete: ...


def process_chapter(filepath: Incomplete, chapter_idx: int, story_id: Incomplete, cursor: Incomplete, nlp: Incomplete, sentiment_pipe: Incomplete) -> None: ...


def process_story(story_dir: str, filepaths: Incomplete, cursor: Cursor, conn: Connection, nlp: Language, sentiment_pipe: Incomplete) -> bool: ...


def main() -> None: ...
