import unittest
import argparse
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

from storybuilder.analysis.generate_embeddings import get_chunks, main


class TestGenerateEmbeddings(unittest.TestCase):
    def test_get_chunks(self):
        text = "This is a simple text that we want to split into smaller chunks"

        # Split into chunks of 3 words
        chunks = get_chunks(text, chunk_size=3)
        self.assertEqual(len(chunks), 5)
        self.assertEqual(chunks[0], "This is a")
        self.assertEqual(chunks[1], "simple text that")
        self.assertEqual(chunks[2], "we want to")
        self.assertEqual(chunks[3], "split into smaller")
        self.assertEqual(chunks[4], "chunks")

    @patch(
        "storybuilder.analysis.generate_embeddings.argparse.ArgumentParser.parse_args"
    )
    @patch("storybuilder.analysis.generate_embeddings.chromadb.PersistentClient")
    @patch("storybuilder.analysis.generate_embeddings.SentenceTransformer")
    @patch("storybuilder.analysis.generate_embeddings.Path.rglob")
    def test_main(
        self, mock_rglob, mock_sentence_transformer, mock_chroma_client, mock_parse_args
    ):
        # 1. Setup mocks
        # Mock CLI arguments
        args = argparse.Namespace(
            limit=2,
            stories_dir="test_stories",
            db_path="./test_chroma_db",
            model="all-MiniLM-L6-v2",
        )
        mock_parse_args.return_value = args

        # Mock Chroma DB client and collections
        mock_client = MagicMock()
        mock_chroma_client.return_value = mock_client
        mock_chunks_collection = MagicMock()
        mock_averages_collection = MagicMock()

        # When get_or_create_collection is called, return different mock collections
        def side_effect(name, metadata=None):
            if name == "story_chunks":
                return mock_chunks_collection
            if name == "story_averages":
                return mock_averages_collection
            raise ValueError(f"Unexpected collection name requested: {name}")

        mock_client.get_or_create_collection.side_effect = side_effect

        # Mock that no existing averages are found to force processing
        mock_averages_collection.get.return_value = {"ids": []}

        # Mock SentenceTransformer
        mock_model = MagicMock()
        mock_sentence_transformer.return_value = mock_model
        # Encode returns a dummy embedding vector for each chunk
        import numpy as np

        # Return a list of two dummy numpy array embeddings because our test file will be split into two chunks
        dummy_embedding_1 = np.array([0.1, 0.2, 0.3])
        dummy_embedding_2 = np.array([0.4, 0.5, 0.6])
        mock_model.encode.return_value = np.array(
            [dummy_embedding_1, dummy_embedding_2]
        )

        # Create a temporary test file to act as a story
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = Path(temp_dir) / "test_story.txt"
            # Write enough words so we get multiple chunks. The chunk size is 250 in the main script.
            # We'll just write 300 words.
            text = " ".join([f"word{i}" for i in range(300)])
            with open(temp_file_path, "w", encoding="utf-8") as f:
                f.write(text)

            # Mock rglob to return our temp file
            mock_rglob.return_value = [temp_file_path]

            # 2. Call the function
            main()

            # 3. Assertions
            # Verify SentenceTransformer was called
            mock_sentence_transformer.assert_called_once()

            # Verify get_or_create_collection was called for both
            mock_client.get_or_create_collection.assert_any_call(
                name="story_chunks", metadata={"hnsw:space": "cosine"}
            )
            mock_client.get_or_create_collection.assert_any_call(
                name="story_averages", metadata={"hnsw:space": "cosine"}
            )

            # Verify chunks collection add was called
            mock_chunks_collection.add.assert_called_once()
            kwargs = mock_chunks_collection.add.call_args[1]
            self.assertIn("ids", kwargs)
            self.assertIn("embeddings", kwargs)
            self.assertIn("documents", kwargs)
            self.assertIn("metadatas", kwargs)

            self.assertEqual(len(kwargs["ids"]), 2)
            self.assertEqual(kwargs["ids"][0], f"{temp_file_path}_chunk_0")
            self.assertEqual(kwargs["ids"][1], f"{temp_file_path}_chunk_1")

            # Verify averages collection add was called
            mock_averages_collection.add.assert_called_once()
            kwargs_avg = mock_averages_collection.add.call_args[1]
            self.assertEqual(kwargs_avg["ids"], [str(temp_file_path)])
            self.assertEqual(kwargs_avg["documents"], [""])
            self.assertEqual(
                kwargs_avg["metadatas"], [{"filepath": str(temp_file_path)}]
            )

    @patch(
        "storybuilder.analysis.generate_embeddings.argparse.ArgumentParser.parse_args"
    )
    @patch("storybuilder.analysis.generate_embeddings.chromadb.PersistentClient")
    @patch("storybuilder.analysis.generate_embeddings.SentenceTransformer")
    @patch("storybuilder.analysis.generate_embeddings.Path.rglob")
    def test_main_skip_existing(
        self, mock_rglob, mock_sentence_transformer, mock_chroma_client, mock_parse_args
    ):
        # Mock CLI arguments
        args = argparse.Namespace(
            limit=2,
            stories_dir="test_stories",
            db_path="./test_chroma_db",
            model="all-MiniLM-L6-v2",
        )
        mock_parse_args.return_value = args

        # Mock Chroma DB client and collections
        mock_client = MagicMock()
        mock_chroma_client.return_value = mock_client
        mock_chunks_collection = MagicMock()
        mock_averages_collection = MagicMock()

        def side_effect(name, metadata=None):
            if name == "story_chunks":
                return mock_chunks_collection
            elif name == "story_averages":
                return mock_averages_collection
            raise AssertionError(f"Unexpected collection name: {name}")

        mock_client.get_or_create_collection.side_effect = side_effect

        # Mock that an existing average is found
        mock_averages_collection.get.return_value = {"ids": ["some_id"]}

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = Path(temp_dir) / "test_story.txt"
            with open(temp_file_path, "w", encoding="utf-8") as f:
                f.write("Some text")

            mock_rglob.return_value = [temp_file_path]

            main()

            # verify no new embeddings are added
            mock_chunks_collection.add.assert_not_called()
            mock_averages_collection.add.assert_not_called()

    @patch(
        "storybuilder.analysis.generate_embeddings.argparse.ArgumentParser.parse_args"
    )
    @patch("storybuilder.analysis.generate_embeddings.chromadb.PersistentClient")
    @patch("storybuilder.analysis.generate_embeddings.SentenceTransformer")
    @patch("storybuilder.analysis.generate_embeddings.Path.rglob")
    def test_main_error_handling(
        self, mock_rglob, mock_sentence_transformer, mock_chroma_client, mock_parse_args
    ):
        # Mock CLI arguments
        args = argparse.Namespace(
            limit=2,
            stories_dir="test_stories",
            db_path="./test_chroma_db",
            model="all-MiniLM-L6-v2",
        )
        mock_parse_args.return_value = args

        # Mock Chroma DB client and collections
        mock_client = MagicMock()
        mock_chroma_client.return_value = mock_client
        mock_chunks_collection = MagicMock()
        mock_averages_collection = MagicMock()

        def side_effect(name, metadata=None):
            if name == "story_chunks":
                return mock_chunks_collection
            elif name == "story_averages":
                return mock_averages_collection

        mock_client.get_or_create_collection.side_effect = side_effect

        # no existing average
        mock_averages_collection.get.return_value = {"ids": []}

        # raise an error on encode
        mock_model = MagicMock()
        mock_sentence_transformer.return_value = mock_model
        mock_model.encode.side_effect = Exception("Test Error")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = Path(temp_dir) / "test_story.txt"
            with open(temp_file_path, "w", encoding="utf-8") as f:
                f.write(
                    "Some text that is long enough to be chunked into at least one chunk because chunk size is 250 in main, but actually we only need a single chunk"
                )

            mock_rglob.return_value = [temp_file_path]

            # Suppress print statement from error handling
            with patch("builtins.print") as mock_print:
                main()

                # Verify error was caught and logged
                error_logged = any(
                    "Error processing" in str(call) for call in mock_print.mock_calls
                )
                self.assertTrue(error_logged)

            # verify no new embeddings are added due to the exception
            mock_chunks_collection.add.assert_not_called()
            mock_averages_collection.add.assert_not_called()


if __name__ == "__main__":
    unittest.main()
