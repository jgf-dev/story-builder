import unittest
from storybuilder.genai.cartesia_client import NAME_FALLBACK_MAP
from storybuilder.genai.cartesia_client import VOICE_MAP
from storybuilder.genai.cartesia_client import parse_speech_config_cartesia
from storybuilder.genai.cartesia_client import parse_transcript_segments


class TestCartesiaClient(unittest.TestCase):
    def test_parse_speech_config_cartesia(self) -> None: ...

    def test_parse_transcript_segments(self) -> None: ...
