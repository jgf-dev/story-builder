import unittest

from storybuilder.genai.client import main as client_main
from storybuilder.genai.client import parse_speech_config
from storybuilder.genai.tts import main as tts_main


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

    def test_parse_speech_config_active_speakers(self):
        # Only Speaker2 and Speaker3 speak, so they should be matched in that order
        markdown_content = """
        ### DIRECTOR'S NOTES
        Style:
        - Speaker1 (Voice: VoiceA): ...
        - Speaker2 (Voice: VoiceB): ...
        - Speaker3 (Voice: VoiceC): ...

        #### TRANSCRIPT
        Speaker2: "Hello!"
        Speaker3: "Hi there!"
        """
        config = parse_speech_config(markdown_content)
        self.assertEqual(len(config), 2)
        self.assertEqual(config[0]["speaker"], "Speaker2")
        self.assertEqual(config[0]["voice"], "VoiceB")
        self.assertEqual(config[1]["speaker"], "Speaker3")
        self.assertEqual(config[1]["voice"], "VoiceC")

    def test_parse_speech_config_active_speaker_no_voice_fallback(self):
        # Speaker3 speaks but has no voice mapping, should fallback to Kore
        markdown_content = """
        ### DIRECTOR'S NOTES
        Style:
        - Speaker1 (Voice: VoiceA): ...
        - Speaker2 (Voice: VoiceB): ...

        #### TRANSCRIPT
        Speaker3: "Hey!"
        """
        config = parse_speech_config(markdown_content)
        self.assertEqual(len(config), 2)
        self.assertEqual(config[0]["speaker"], "Speaker3")
        self.assertEqual(config[0]["voice"], "Kore")
        self.assertEqual(config[1]["speaker"], "Dummy")
        self.assertEqual(config[1]["voice"], "Puck")

    def test_parse_speech_config_active_speaker_padded(self):
        # Only Speaker1 speaks, should be padded with Dummy Puck
        markdown_content = """
        ### DIRECTOR'S NOTES
        Style:
        - Speaker1 (Voice: VoiceA): ...
        - Speaker2 (Voice: VoiceB): ...

        #### TRANSCRIPT
        Speaker1: "Just me talking."
        """
        config = parse_speech_config(markdown_content)
        self.assertEqual(len(config), 2)
        self.assertEqual(config[0]["speaker"], "Speaker1")
        self.assertEqual(config[0]["voice"], "VoiceA")
        self.assertEqual(config[1]["speaker"], "Dummy")
        self.assertEqual(config[1]["voice"], "Puck")

    def test_extract_markdown_block(self):
        from unittest.mock import patch

        # We patch Client and sys.exit to allow importing fix_prompts safely
        with (
            patch("google.genai.Client"),
            patch("os.getenv", return_value="fake_key"),
            patch("sys.exit"),
        ):
            from storybuilder.genai.fix_prompts import extract_markdown_block

            # 1. With markdown block
            content = "```markdown\nhello world\n```"
            self.assertEqual(extract_markdown_block(content), "hello world")

            # 2. With generic code block
            content = '```json\n{"a": 1}\n```'
            self.assertEqual(extract_markdown_block(content), '{"a": 1}')

            # 3. Without block
            content = "just raw text"
            self.assertEqual(extract_markdown_block(content), "just raw text")

            # 4. Fallback code block cleanup
            content = "```\nfallback content\n```"
            self.assertEqual(extract_markdown_block(content), "fallback content")

    def test_tts_entrypoint_resolves_to_client_main(self):
        """Verify that storybuilder.genai.tts:main re-exports client.main correctly."""
        self.assertIs(tts_main, client_main)


if __name__ == "__main__":
    unittest.main()
