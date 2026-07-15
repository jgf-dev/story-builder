from _typeshed import Incomplete

import sys
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch
from storybuilder.analysis.find_similar import main


class TestFindSimilar(unittest.TestCase):
    @patch("sys.stdout", new_callable=StringIO)
    @patch("storybuilder.analysis.find_similar.chromadb.PersistentClient")
    @patch("sys.argv", ["find_similar.py", "test_story.txt"])
    def test_missing_collection_error(self, mock_client_class: Incomplete, mock_stdout: Incomplete) -> None: ...

    @patch("storybuilder.analysis.find_similar.chromadb.PersistentClient")
    @patch("storybuilder.analysis.find_similar.argparse.ArgumentParser.parse_args")
    def test_missing_story_result_none(self, mock_parse_args: Incomplete, mock_chroma_client: Incomplete) -> None: ...

    @patch("storybuilder.analysis.find_similar.chromadb.PersistentClient")
    @patch("storybuilder.analysis.find_similar.argparse.ArgumentParser.parse_args")
    def test_missing_story_embeddings_none(self, mock_parse_args: Incomplete, mock_chroma_client: Incomplete) -> None: ...

    @patch("storybuilder.analysis.find_similar.chromadb.PersistentClient")
    @patch("storybuilder.analysis.find_similar.argparse.ArgumentParser.parse_args")
    def test_missing_story_embeddings_empty_list(self, mock_parse_args: Incomplete, mock_chroma_client: Incomplete) -> None: ...
