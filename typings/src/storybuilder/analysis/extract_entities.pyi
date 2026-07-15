from _typeshed import Incomplete

import argparse
import sqlite3
from argparse import Namespace
from collections import Counter
from pathlib import Path
from sqlite3 import Connection, Cursor
import spacy
from spacy.language import Language
from thinc.api import require_gpu, set_gpu_allocator
from tqdm import tqdm

DB_PATH: Literal['stories/db/nlp_analysis.db'] = "stories/db/nlp_analysis.db"
ALLOWED_LABELS: set[str]


def init_db(db_path: Incomplete) -> Connection: ...


def is_processed(cursor: Cursor, filepath: str) -> Incomplete: ...


def parse_args() -> Namespace: ...


def load_spacy_model(model_name: Incomplete, use_gpu: Incomplete) -> Language | None: ...


def process_file(filepath_str: str, nlp: Language, cursor: Cursor) -> None: ...


def main() -> None: ...
