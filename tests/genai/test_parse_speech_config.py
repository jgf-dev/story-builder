import unittest

from storybuilder.genai.client import parse_speech_config


class TestParseSpeechConfig(unittest.TestCase):
    def test_parse_speech_config(self):
        markdown_content = """
* John (Voice: VoiceA)
* Jane (Voice: VoiceB)

#### TRANSCRIPT
John: Hello!
Jane: Hi!
"""
        config = parse_speech_config(markdown_content)
        self.assertEqual(
            config,
            [
                {"speaker": "John", "voice": "VoiceA"},
                {"speaker": "Jane", "voice": "VoiceB"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
