import unittest
from unittest.mock import patch, MagicMock

from storybuilder.analysis.extract_entities import load_spacy_model


class TestExtractEntities(unittest.TestCase):
    @patch("storybuilder.analysis.extract_entities.spacy.load")
    @patch("storybuilder.analysis.extract_entities.spacy.require_gpu")
    @patch("storybuilder.analysis.extract_entities.require_gpu")
    @patch("storybuilder.analysis.extract_entities.set_gpu_allocator")
    def test_load_spacy_model_with_gpu(
        self,
        mock_set_gpu_allocator,
        mock_require_gpu_thinc,
        mock_require_gpu_spacy,
        mock_spacy_load,
    ):
        # Setup mock nlp object
        mock_nlp = MagicMock()
        mock_spacy_load.return_value = mock_nlp

        # Call function
        result = load_spacy_model("en_core_web_lg", True)

        # Assertions
        mock_set_gpu_allocator.assert_called_once_with("pytorch")
        mock_require_gpu_thinc.assert_called_once_with(0)
        mock_require_gpu_spacy.assert_called_once()
        mock_spacy_load.assert_called_once_with("en_core_web_lg")

        mock_nlp.select_pipes.assert_called_once_with(
            enable=["tagger", "parser", "ner"]
        )
        mock_nlp.add_pipe.assert_any_call("merge_noun_chunks")
        mock_nlp.add_pipe.assert_any_call("merge_entities")
        self.assertEqual(mock_nlp.max_length, 5000000)

        self.assertEqual(result, mock_nlp)

    @patch("storybuilder.analysis.extract_entities.spacy.load")
    @patch("storybuilder.analysis.extract_entities.spacy.require_gpu")
    @patch("storybuilder.analysis.extract_entities.require_gpu")
    @patch("storybuilder.analysis.extract_entities.set_gpu_allocator")
    def test_load_spacy_model_without_gpu(
        self,
        mock_set_gpu_allocator,
        mock_require_gpu_thinc,
        mock_require_gpu_spacy,
        mock_spacy_load,
    ):
        # Setup mock nlp object
        mock_nlp = MagicMock()
        mock_spacy_load.return_value = mock_nlp

        # Call function
        result = load_spacy_model("en_core_web_lg", False)

        # Assertions
        mock_set_gpu_allocator.assert_not_called()
        mock_require_gpu_thinc.assert_not_called()
        mock_require_gpu_spacy.assert_not_called()
        mock_spacy_load.assert_called_once_with("en_core_web_lg")

        mock_nlp.select_pipes.assert_called_once_with(
            enable=["tagger", "parser", "ner"]
        )
        mock_nlp.add_pipe.assert_any_call("merge_noun_chunks")
        mock_nlp.add_pipe.assert_any_call("merge_entities")
        self.assertEqual(mock_nlp.max_length, 5000000)

        self.assertEqual(result, mock_nlp)

    @patch("builtins.print")
    @patch("storybuilder.analysis.extract_entities.spacy.load")
    def test_load_spacy_model_oserror(self, mock_spacy_load, mock_print):
        # Setup mock to raise OSError
        mock_spacy_load.side_effect = OSError("Model not found")

        # Call function
        result = load_spacy_model("en_core_web_lg", False)

        # Assertions
        mock_spacy_load.assert_called_once_with("en_core_web_lg")
        mock_print.assert_any_call("Model 'en_core_web_lg' not found.")
        mock_print.assert_any_call(
            "Please run: python -m spacy download en_core_web_lg"
        )
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
