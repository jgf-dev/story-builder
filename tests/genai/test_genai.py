import unittest
from unittest.mock import patch

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

            # 5. Large input with no matching closing block (originally caused backtracking)
            content = "```markdown\n" + "a" * 5000 + "\nnot_matching"
            self.assertEqual(extract_markdown_block(content), "a" * 5000 + "\nnot_matching")
    def test_tts_entrypoint_resolves_to_client_main(self):
        """Verify that storybuilder.genai.tts:main re-exports client.main correctly."""
        self.assertIs(tts_main, client_main)

    def test_main_processes_existing_directory(self):
        """main() should call process_directory when the given --dir exists."""
        with (
            patch("storybuilder.genai.client.process_directory") as mock_process,
            patch("sys.argv", ["genai-tts", "--dir", "/tmp"]),
        ):
            client_main()
            mock_process.assert_called_once_with("/tmp")

    def test_main_exits_nonzero_for_missing_directory(self) -> None:
        """main() should exit non-zero and not call process_directory for a non-existent dir."""
        import io
        from contextlib import redirect_stderr

        stderr = io.StringIO()
        with (
            patch("storybuilder.genai.client.process_directory") as mock_process,
            patch("sys.argv", ["genai-tts", "--dir", "/nonexistent_dir_xyz"]),
            redirect_stderr(stderr),
            self.assertRaises(SystemExit) as raised,
        ):
            client_main()

        mock_process.assert_not_called()
        self.assertNotEqual(raised.exception.code, 0)
        self.assertIn("/nonexistent_dir_xyz", stderr.getvalue())
=======
            # 5. Large input with no matching closing block (originally caused backtracking)
            content = "```markdown\n" + "a" * 5000 + "\nnot_matching"
            self.assertEqual(extract_markdown_block(content), "a" * 5000 + "\nnot_matching")
>>>>>>> fix-genai-tts-entrypoint-9568411881905231847


if __name__ == "__main__":
    unittest.main()
