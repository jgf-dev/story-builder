from _typeshed import Incomplete

from sqlite3 import Cursor
from sqlite3 import Connection
from spacy.language import Language
from argparse import Namespace
import argparse
import sqlite3
from collections import Counter
from pathlib import Path
import spacy
from thinc.api import require_gpu
from thinc.api import set_gpu_allocator
from tqdm import tqdm

DB_PATH: Literal['nlp_analysis.db'] = "nlp_analysis.db"
ALLOWED_LABELS: set[str]


def init_db(db_path: Incomplete) -> Connection: ...


def is_processed(cursor: Cursor, filepath: str) -> Incomplete: ...


def parse_args() -> Namespace: ...


def load_spacy_model(model_name: Incomplete, use_gpu: Incomplete) -> Language | None: ...


def process_file(filepath_str: str, nlp: Language, cursor: Cursor) -> None: ...


def main() -> None: ...
