import argparse
import logging
import os
import sqlite3
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from storybuilder.downloader.db import (
	_parse_author,  # pyrefly: ignore [private-import]
	_parse_output_path,  # pyrefly: ignore [private-import]
	optimize_fts,
)
from storybuilder.downloader.db import init_db as _db_init_db

logger: Logger
BATCH_SIZE: Literal[1000] = 1000


def init_db(db_path: str) -> sqlite3.Connection: ...


def parse_header(filepath: str) -> "dict | None": ...


def import_files(conn: sqlite3.Connection, files: list[str], force: bool = False, start_time: float | None = None) -> tuple[int, int]: ...


def main() -> None: ...
