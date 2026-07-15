import argparse
import os
import sqlite3
import sys
import time
from pathlib import Path
from storybuilder.downloader.db import _parse_author
from storybuilder.downloader.db import _parse_output_path
from storybuilder.downloader.db import init_db as _db_init_db
from storybuilder.downloader.db import optimize_fts

BATCH_SIZE: Literal[1000] = 1000


def init_db(db_path: str) -> sqlite3.Connection: ...


def parse_header(filepath: str) -> "dict | None": ...


def import_files(conn: sqlite3.Connection, files: list[str], force: bool = False) -> tuple[int, int]: ...


def main() -> None: ...
