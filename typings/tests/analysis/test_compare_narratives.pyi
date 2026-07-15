import unittest
import sqlite3
import tempfile
import shutil
import sys
import io
import warnings
from unittest.mock import patch
from pathlib import Path
from storybuilder.analysis.compare_narratives import main


class TestCompareNarratives(unittest.TestCase):
    def setUp(self) -> None: ...

    def tearDown(self) -> None: ...

    def test_insufficient_stories(self) -> None: ...

    def test_skip_short_stories(self) -> None: ...

    def test_successful_clustering(self) -> None: ...
