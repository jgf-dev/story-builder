from _typeshed import Incomplete

import argparse
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch
from storybuilder.analysis.generate_embeddings import get_chunks
from storybuilder.analysis.generate_embeddings import main


class TestGenerateEmbeddings(unittest.TestCase):
    def test_get_chunks(self) -> None: ...

    @patch(
        "storybuilder.analysis.generate_embeddings.argparse.ArgumentParser.parse_args"
    )
    @patch("storybuilder.analysis.generate_embeddings.chromadb.PersistentClient")
    @patch("storybuilder.analysis.generate_embeddings.SentenceTransformer")
    @patch("storybuilder.analysis.generate_embeddings.Path.rglob")
    def test_main(self, mock_rglob: Incomplete, mock_sentence_transformer: Incomplete, mock_chroma_client: Incomplete, mock_parse_args: Incomplete) -> None: ...

    @patch(
        "storybuilder.analysis.generate_embeddings.argparse.ArgumentParser.parse_args"
    )
    @patch("storybuilder.analysis.generate_embeddings.chromadb.PersistentClient")
    @patch("storybuilder.analysis.generate_embeddings.SentenceTransformer")
    @patch("storybuilder.analysis.generate_embeddings.Path.rglob")
    def test_main_skip_existing(self, mock_rglob: Incomplete, mock_sentence_transformer: Incomplete, mock_chroma_client: Incomplete, mock_parse_args: Incomplete) -> None: ...

    @patch(
        "storybuilder.analysis.generate_embeddings.argparse.ArgumentParser.parse_args"
    )
    @patch("storybuilder.analysis.generate_embeddings.chromadb.PersistentClient")
    @patch("storybuilder.analysis.generate_embeddings.SentenceTransformer")
    @patch("storybuilder.analysis.generate_embeddings.Path.rglob")
    def test_main_error_handling(self, mock_rglob: Incomplete, mock_sentence_transformer: Incomplete, mock_chroma_client: Incomplete, mock_parse_args: Incomplete) -> None: ...
