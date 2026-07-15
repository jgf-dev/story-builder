import unittest
from storybuilder.genai.cartesia_client import (
    parse_speech_config_cartesia,
    parse_transcript_segments,
    VOICE_MAP,
    NAME_FALLBACK_MAP,
)


class TestCartesiaClient(unittest.TestCase):
    def test_parse_speech_config_cartesia(self) -> None: ...

    def test_parse_transcript_segments(self) -> None: ...
