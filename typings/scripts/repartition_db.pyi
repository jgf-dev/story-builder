from _typeshed import Incomplete

import glob
import shutil
import sqlite3
import sys
from pathlib import Path
from storybuilder.downloader.db import INDEXES
from storybuilder.downloader.db import SCHEMA


def get_db_filename_from_date(story_date: Incomplete) -> str: ...


def get_or_create_connection(temp_dir: Path, filename: str, new_conns: dict) -> sqlite3.Connection: ...


def process_source_database(src_path: str, temp_dir: Path, new_conns: dict) -> int: ...


def finalize_new_databases(new_conns: dict) -> None: ...


def swap_db_directories(db_path: Path, temp_dir: Path) -> None: ...


def repartition_dbs(db_dir: str) -> None: ...
