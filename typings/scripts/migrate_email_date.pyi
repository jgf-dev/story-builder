import argparse
import sqlite3
import sys
from pathlib import Path
from storybuilder.downloader.db import INDEXES
from storybuilder.downloader.db import SCHEMA
from storybuilder.downloader.db import migrate_legacy_schema


def main() -> None: ...
