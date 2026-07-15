from _typeshed import Incomplete

from argparse import Namespace
import argparse
import os
import sqlite3
import sys
from pathlib import Path


def connect(db_path: str) -> sqlite3.Connection: ...


def cmd_search(conn: sqlite3.Connection, args: Incomplete, db_paths: "list[str] | None" = None) -> None: ...


def cmd_get(conn: sqlite3.Connection, args: Incomplete, db_paths: "list[str] | None" = None) -> None: ...


def cmd_list(conn: sqlite3.Connection, args: Incomplete, db_paths: "list[str] | None" = None) -> None: ...


def cmd_stats(conn: sqlite3.Connection, args: Incomplete, db_paths: "list[str] | None" = None) -> None: ...


def main() -> None: ...
