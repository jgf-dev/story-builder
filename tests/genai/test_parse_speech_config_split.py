import unittest

from storybuilder.genai.client import _build_speech_config
from storybuilder.genai.client import _extract_active_speakers
from storybuilder.genai.client import _parse_voice_mappings


class TestParseSpeechConfigSplit(unittest.TestCase):
    def test_parse_voice_mappings(self) -> None:
        preamble = """
        * John (Voice: VoiceA)
        - Jane (Voice: VoiceB)
        """
        mappings, speakers, transcript = _parse_voice_mappings(preamble)
        self.assertEqual(mappings, {"John": "VoiceA", "Jane": "VoiceB"})
        self.assertEqual(speakers, ["John", "Jane"])
        self.assertEqual(transcript, "")

    def test_extract_active_speakers(self) -> None:
        transcript = """
        John: Hello!
        Jane: Hi!
        John: How are you?
        """
        speakers = _extract_active_speakers(transcript)
        self.assertEqual(speakers, ["John", "Jane"])

    def test_build_speech_config(self) -> None:
        active_speakers = ["John", "Jane"]
        speaker_to_voice = {"John": "VoiceA", "Jane": "VoiceB"}
        config = _build_speech_config(active_speakers, speaker_to_voice)
        self.assertEqual(
            config,
            [
                {"speaker": "John", "voice": "VoiceA"},
                {"speaker": "Jane", "voice": "VoiceB"},
            ],
        )

    def test_build_speech_config_fallback_active(self) -> None:
        active_speakers = ["John", "Bob"]
        speaker_to_voice = {"John": "VoiceA"}
        config = _build_speech_config(active_speakers, speaker_to_voice)
        self.assertEqual(
            config,
            [
                {"speaker": "John", "voice": "VoiceA"},
                {"speaker": "Bob", "voice": "Kore"},
            ],
        )

    def test_build_speech_config_fallback_preamble(self) -> None:
        active_speakers = []
        speaker_to_voice = {"John": "VoiceA", "Jane": "VoiceB"}
        config = _build_speech_config(active_speakers, speaker_to_voice)
        self.assertEqual(
            config,
            [
                {"speaker": "John", "voice": "VoiceA"},
                {"speaker": "Jane", "voice": "VoiceB"},
            ],
        )

    def test_build_speech_config_single(self) -> None:
        active_speakers = ["John"]
        speaker_to_voice = {"John": "VoiceA"}
        config = _build_speech_config(active_speakers, speaker_to_voice)
        self.assertEqual(
            config,
            [
                {"speaker": "John", "voice": "VoiceA"},
                {"speaker": "Dummy", "voice": "Puck"},
            ],
        )

    def test_build_speech_config_empty(self) -> None:
        active_speakers = []
        speaker_to_voice = {}
        config = _build_speech_config(active_speakers, speaker_to_voice)
        self.assertEqual(config, [{"voice": "Kore"}])


if __name__ == "__main__":
    unittest.main()
