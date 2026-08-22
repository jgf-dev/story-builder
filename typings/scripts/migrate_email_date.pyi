import argparse
import sqlite3
import sys
from pathlib import Path
from storybuilder.downloader.db import INDEXES, SCHEMA, migrate_legacy_schema


def main() -> None: ...
