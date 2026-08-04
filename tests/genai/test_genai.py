import unittest
from unittest.mock import patch

import pytest

from storybuilder.genai.client import main as client_main
from storybuilder.genai.client import parse_speech_config
from storybuilder.genai.tts import main as tts_main


class TestGenAIClient(unittest.TestCase):
    def test_parse_speech_config_multi_speaker(self) -> None:
        markdown_content = """
        ### DIRECTOR'S NOTES
        Style:
        - Jace (Voice: Algenib): 27-year-old.
        - Levi (Voice: Zubenelgenubi): 20-year-old.
        """
        config = parse_speech_config(markdown_content)
        assert len(config) == 2
        assert config[0]["speaker"] == "Jace"
        assert config[0]["voice"] == "Algenib"
        assert config[1]["speaker"] == "Levi"
        assert config[1]["voice"] == "Zubenelgenubi"

    def test_parse_speech_config_single_speaker(self) -> None:
        # A single speaker should be padded with a Dummy speaker to force multi-speaker mode
        markdown_content = """
        ### DIRECTOR'S NOTES
        Style:
        * Narrator (Voice: Kore): The narrator voice.
        """
        config = parse_speech_config(markdown_content)
        assert len(config) == 2
        assert config[0]["speaker"] == "Narrator"
        assert config[0]["voice"] == "Kore"
        assert config[1]["speaker"] == "Dummy"
        assert config[1]["voice"] == "Puck"

    def test_parse_speech_config_no_speakers(self) -> None:
        # When no speakers are found, it should fallback to a single generic voice
        markdown_content = """
        ### DIRECTOR'S NOTES
        Style: Just talk normally.
        """
        config = parse_speech_config(markdown_content)
        assert len(config) == 1
        assert "speaker" not in config[0]
        assert config[0]["voice"] == "Kore"

    def test_parse_speech_config_max_two_voices(self) -> None:
        # It should ignore any voices beyond the first two
        markdown_content = """
        ### DIRECTOR'S NOTES
        Style:
        - Speaker1 (Voice: VoiceA): ...
        - Speaker2 (Voice: VoiceB): ...
        - Speaker3 (Voice: VoiceC): ...
        """
        config = parse_speech_config(markdown_content)
        assert len(config) == 2
        assert config[0]["speaker"] == "Speaker1"
        assert config[0]["voice"] == "VoiceA"
        assert config[1]["speaker"] == "Speaker2"
        assert config[1]["voice"] == "VoiceB"

    def test_parse_speech_config_active_speakers(self) -> None:
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
        assert len(config) == 2
        assert config[0]["speaker"] == "Speaker2"
        assert config[0]["voice"] == "VoiceB"
        assert config[1]["speaker"] == "Speaker3"
        assert config[1]["voice"] == "VoiceC"

    def test_parse_speech_config_active_speaker_no_voice_fallback(self) -> None:
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
        assert len(config) == 2
        assert config[0]["speaker"] == "Speaker3"
        assert config[0]["voice"] == "Kore"
        assert config[1]["speaker"] == "Dummy"
        assert config[1]["voice"] == "Puck"

    def test_parse_speech_config_active_speaker_padded(self) -> None:
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
        assert len(config) == 2
        assert config[0]["speaker"] == "Speaker1"
        assert config[0]["voice"] == "VoiceA"
        assert config[1]["speaker"] == "Dummy"
        assert config[1]["voice"] == "Puck"

    def test_extract_markdown_block(self) -> None:
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
            assert extract_markdown_block(content) == "hello world"

            # 2. With generic code block
            content = '```json\n{"a": 1}\n```'
            assert extract_markdown_block(content) == '{"a": 1}'

            # 3. Without block
            content = "just raw text"
            assert extract_markdown_block(content) == "just raw text"

            # 4. Fallback code block cleanup
            content = "```\nfallback content\n```"
            assert extract_markdown_block(content) == "fallback content"
            # 5. Large input with no matching closing block (originally caused backtracking)
            content = "```markdown\n" + "a" * 5000 + "\nnot_matching"
            assert extract_markdown_block(content) == "a" * 5000 + "\nnot_matching"

            # 5. Large input with no matching closing block (originally caused backtracking)
            content = "```markdown\n" + "a" * 5000 + "\nnot_matching"
            assert extract_markdown_block(content) == "a" * 5000 + "\nnot_matching"

    def test_tts_entrypoint_resolves_to_client_main(self) -> None:
        """Verify that storybuilder.genai.tts:main re-exports client.main correctly."""
        assert tts_main is client_main

    def test_main_processes_existing_directory(self) -> None:
        """main() should call process_directory when the given --dir exists."""
        with (
            patch("storybuilder.genai.client.process_directory") as mock_process,
            patch("storybuilder.genai.client.get_gemini_api_keys", return_value=[("GEMINI_API_KEY", "fake")]),
            patch("storybuilder.genai.client.glob.glob", return_value=["/tmp/01-part.md"]),
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
            patch("storybuilder.genai.client.get_gemini_api_keys", return_value=[("GEMINI_API_KEY", "fake")]),
            patch("sys.argv", ["genai-tts", "--dir", "/nonexistent_dir_xyz"]),
            redirect_stderr(stderr),
            pytest.raises(SystemExit) as raised,
        ):
            client_main()

        mock_process.assert_not_called()
        assert raised.value.code != 0
        assert "/nonexistent_dir_xyz" in stderr.getvalue()

    def test_get_gemini_api_keys_primary_only(self) -> None:
        from storybuilder.genai.client import get_gemini_api_keys
        with patch.dict("os.environ", {"GEMINI_API_KEY": "primary-key"}, clear=True):
            keys = get_gemini_api_keys()
            self.assertEqual(len(keys), 1)
            self.assertEqual(keys[0], ("GEMINI_API_KEY", "primary-key"))

    def test_get_gemini_api_keys_with_rotations(self) -> None:
        from storybuilder.genai.client import get_gemini_api_keys
        env = {
            "GEMINI_API_KEY": "primary",
            "GEMINI_API_KEY_1": "key1",
            "GEMINI_API_KEY_2": "key2",
        }
        with patch.dict("os.environ", env, clear=True):
            keys = get_gemini_api_keys()
            self.assertEqual(len(keys), 3)
            self.assertEqual(keys[1], ("GEMINI_API_KEY_1", "key1"))

    def test_apikey_rotator(self) -> None:
        from storybuilder.genai.client import ApiKeyRotator
        keys = [("KEY1", "val1"), ("KEY2", "val2")]

        with patch("google.genai.Client") as mock_client:
            rotator = ApiKeyRotator(keys)
            self.assertEqual(rotator.current_key_name, "KEY1")
            self.assertEqual(rotator.total_keys, 2)

            rotator.rotate()
            self.assertEqual(rotator.current_key_name, "KEY2")
            mock_client.assert_called_with(api_key="val2")

            rotator.rotate()
            self.assertEqual(rotator.current_key_name, "KEY1")
            mock_client.assert_called_with(api_key="val1")

    def test_handle_exception_404(self) -> None:
        from storybuilder.genai.client import ApiKeyRotator
        from storybuilder.genai.client import _handle_exception
        keys = [("KEY1", "val1")]

        with patch("google.genai.Client"):
            rotator = ApiKeyRotator(keys)

            # 404 should drop the previous_id
            class MockException(Exception):
                pass

            e = MockException("404 Session not found")
            prev_id, keys_tried, attempt, should_continue = _handle_exception(
                e, rotator, "old_session_id", 0, 0, "test.md"
            )

            self.assertIsNone(prev_id)
            self.assertTrue(should_continue)

    @patch("time.sleep")
    def test_handle_exception_quota_rotation(self, mock_sleep) -> None:
        from storybuilder.genai.client import ApiKeyRotator
        from storybuilder.genai.client import _handle_exception
        keys = [("KEY1", "val1"), ("KEY2", "val2")]

        with patch("google.genai.Client"):
            rotator = ApiKeyRotator(keys)
            self.assertEqual(rotator.current_key_name, "KEY1")

            class MockException(Exception):
                pass

            e = MockException("429 Too Many Requests")
            prev_id, keys_tried, attempt, should_continue = _handle_exception(
                e, rotator, "active_session", 0, 0, "test.md"
            )

            # With the new backoff behavior, the key should NOT rotate on 429
            # Instead, it waits and retries on the same key with attempt + 1
            self.assertEqual(prev_id, "active_session")
            self.assertEqual(keys_tried, 0)
            self.assertEqual(attempt, 1)
            self.assertTrue(should_continue)
            self.assertEqual(rotator.current_key_name, "KEY1")
            mock_sleep.assert_called_with(15)


if __name__ == "__main__":
    unittest.main()
