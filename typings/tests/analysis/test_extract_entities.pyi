from _typeshed import Incomplete

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch
from storybuilder.analysis.extract_entities import get_processed_files
from storybuilder.analysis.extract_entities import init_db
from storybuilder.analysis.extract_entities import main


class TestExtractEntities(unittest.TestCase):
    conn: Connection
    db_fd: int
    db_path: str
    stories_dir: TemporaryDirectory[str]

    def setUp(self) -> None: ...

    def tearDown(self) -> None: ...

    def test_init_db(self) -> None: ...

    def test_get_processed_files(self) -> None: ...

    @patch("argparse.ArgumentParser.parse_args")
    @patch("spacy.load")
    @patch("storybuilder.analysis.extract_entities.require_gpu")
    @patch("storybuilder.analysis.extract_entities.set_gpu_allocator")
    def test_main_happy_path(self, mock_set_gpu: Incomplete, mock_require_gpu: Incomplete, mock_spacy_load: Incomplete, mock_parse_args: Incomplete) -> None: ...

    @patch("argparse.ArgumentParser.parse_args")
    @patch("spacy.load")
    def test_main_skip_processed(self, mock_spacy_load: Incomplete, mock_parse_args: Incomplete) -> None: ...

    @patch("argparse.ArgumentParser.parse_args")
    @patch("spacy.load")
    def test_main_force_reprocess(self, mock_spacy_load: Incomplete, mock_parse_args: Incomplete) -> None: ...

    @patch("argparse.ArgumentParser.parse_args")
    @patch("spacy.load")
    def test_main_model_not_found(self, mock_spacy_load: Incomplete, mock_parse_args: Incomplete) -> None: ...

    @patch("argparse.ArgumentParser.parse_args")
    @patch("spacy.load")
    @patch("storybuilder.analysis.extract_entities.require_gpu")
    @patch("storybuilder.analysis.extract_entities.set_gpu_allocator")
    @patch("spacy.require_gpu")
    def test_main_with_gpu(self, mock_spacy_require_gpu: Incomplete, mock_set_gpu: Incomplete, mock_require_gpu: Incomplete, mock_spacy_load: Incomplete, mock_parse_args: Incomplete) -> None: ...

    @patch("argparse.ArgumentParser.parse_args")
    @patch("spacy.load")
    def test_main_error_processing_file(self, mock_spacy_load: Incomplete, mock_parse_args: Incomplete) -> None: ...

    @patch("storybuilder.analysis.extract_entities.spacy.load")
    @patch("storybuilder.analysis.extract_entities.spacy.require_gpu")
    @patch("storybuilder.analysis.extract_entities.require_gpu")
    @patch("storybuilder.analysis.extract_entities.set_gpu_allocator")
    def test_load_spacy_model_with_gpu(self, mock_set_gpu_allocator: Incomplete, mock_require_gpu_thinc: Incomplete, mock_require_gpu_spacy: Incomplete, mock_spacy_load: Incomplete) -> None: ...

    @patch("storybuilder.analysis.extract_entities.spacy.load")
    @patch("storybuilder.analysis.extract_entities.spacy.require_gpu")
    @patch("storybuilder.analysis.extract_entities.require_gpu")
    @patch("storybuilder.analysis.extract_entities.set_gpu_allocator")
    def test_load_spacy_model_without_gpu(self, mock_set_gpu_allocator: Incomplete, mock_require_gpu_thinc: Incomplete, mock_require_gpu_spacy: Incomplete, mock_spacy_load: Incomplete) -> None: ...

    @patch("builtins.print")
    @patch("storybuilder.analysis.extract_entities.spacy.load")
    def test_load_spacy_model_oserror(self, mock_spacy_load: Incomplete, mock_print: Incomplete) -> None: ...
