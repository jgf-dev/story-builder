import io
import shutil
import sqlite3
import sys
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest.mock import patch
from storybuilder.analysis.compare_narratives import main


class TestCompareNarratives(unittest.TestCase):
    conn: Connection
    db_path: str
    temp_dir: str

    def setUp(self) -> None: ...

    def tearDown(self) -> None: ...

    def test_insufficient_stories(self) -> None: ...

    def test_skip_short_stories(self) -> None: ...

    def test_successful_clustering(self) -> None: ...
