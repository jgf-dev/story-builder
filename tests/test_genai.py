import unittest
from storybuilder.genai.client import parse_speech_config

class TestGenAIClient(unittest.TestCase):
    def test_parse_speech_config_multi_speaker(self):
        markdown_content = """
        ### DIRECTOR'S NOTES
        Style:
        - Jace (Voice: Algenib): 27-year-old.
        - Levi (Voice: Zubenelgenubi): 20-year-old.
        """
        config = parse_speech_config(markdown_content)
        self.assertEqual(len(config), 2)
        self.assertEqual(config[0]["speaker"], "Jace")
        self.assertEqual(config[0]["voice"], "Algenib")
        self.assertEqual(config[1]["speaker"], "Levi")
        self.assertEqual(config[1]["voice"], "Zubenelgenubi")

    def test_parse_speech_config_single_speaker(self):
        # A single speaker should be padded with a Dummy speaker to force multi-speaker mode
        markdown_content = """
        ### DIRECTOR'S NOTES
        Style:
        * Narrator (Voice: Kore): The narrator voice.
        """
        config = parse_speech_config(markdown_content)
        self.assertEqual(len(config), 2)
        self.assertEqual(config[0]["speaker"], "Narrator")
        self.assertEqual(config[0]["voice"], "Kore")
        self.assertEqual(config[1]["speaker"], "Dummy")
        self.assertEqual(config[1]["voice"], "Puck")

    def test_parse_speech_config_no_speakers(self):
        # When no speakers are found, it should fallback to a single generic voice
        markdown_content = """
        ### DIRECTOR'S NOTES
        Style: Just talk normally.
        """
        config = parse_speech_config(markdown_content)
        self.assertEqual(len(config), 1)
        self.assertNotIn("speaker", config[0])
        self.assertEqual(config[0]["voice"], "Kore")

    def test_parse_speech_config_max_two_voices(self):
        # It should ignore any voices beyond the first two
        markdown_content = """
        ### DIRECTOR'S NOTES
        Style:
        - Speaker1 (Voice: VoiceA): ...
        - Speaker2 (Voice: VoiceB): ...
        - Speaker3 (Voice: VoiceC): ...
        """
        config = parse_speech_config(markdown_content)
        self.assertEqual(len(config), 2)
        self.assertEqual(config[0]["speaker"], "Speaker1")
        self.assertEqual(config[0]["voice"], "VoiceA")
        self.assertEqual(config[1]["speaker"], "Speaker2")
        self.assertEqual(config[1]["voice"], "VoiceB")

if __name__ == "__main__":
    unittest.main()
