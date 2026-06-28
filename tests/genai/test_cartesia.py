from unittest.mock import patch
import unittest
from storybuilder.genai.cartesia_client import (
    parse_speech_config_cartesia,
    parse_transcript_segments,
    VOICE_MAP,
    NAME_FALLBACK_MAP,
)


class TestCartesiaClient(unittest.TestCase):
    def test_parse_speech_config_cartesia(self):
        markdown_content = """
        ### DIRECTOR'S NOTES
        Style:
        - Jace (Voice: Algenib): 27-year-old.
        - Levi (Voice: Kyle): 20-year-old.
        - Kerry (Voice: 6ccbfb76-1fc6-48f7-b71d-91ac6298247b): Custom UUID.
        """
        config = parse_speech_config_cartesia(markdown_content)

        self.assertEqual(config["Jace"], VOICE_MAP["algenib"])
        self.assertEqual(config["Levi"], VOICE_MAP["kyle"])
        self.assertEqual(config["Kerry"], "6ccbfb76-1fc6-48f7-b71d-91ac6298247b")

    def test_parse_transcript_segments(self):
        markdown_content = """# AUDIO PROFILE
        ### DIRECTOR'S NOTES
        - Jace (Voice: Algenib)
        
        #### TRANSCRIPT
        Jace: Hello, my name is Jace.
        Jace: And this is my second line.
        Narrator: This is the narrator speaking here.
        Levi: Hey, Levi here!
        Jace: Back to Jace.
        """
        speaker_to_voice_id = {
            "Jace": "jace-voice-uuid",
            "Narrator": "narrator-voice-uuid",
        }

        # Levi has no explicit definition in speaker_to_voice_id, should fallback to NAME_FALLBACK_MAP or default_voice_id
        segments = parse_transcript_segments(
            markdown_content, speaker_to_voice_id, default_voice_id="default-voice-uuid"
        )

        # Check segment grouping (the two Jace lines are adjacent and should be grouped together!)
        self.assertEqual(len(segments), 4)

        # Segment 1: Jace lines grouped
        self.assertEqual(segments[0][0], "jace-voice-uuid")
        self.assertEqual(
            segments[0][1], "Hello, my name is Jace. And this is my second line."
        )

        # Segment 2: Narrator
        self.assertEqual(segments[1][0], "narrator-voice-uuid")
        self.assertEqual(segments[1][1], "This is the narrator speaking here.")

        # Segment 3: Levi fallback
        self.assertEqual(segments[2][0], NAME_FALLBACK_MAP["levi"])
        self.assertEqual(segments[2][1], "Hey, Levi here!")

        # Segment 4: Jace
        self.assertEqual(segments[3][0], "jace-voice-uuid")
        self.assertEqual(segments[3][1], "Back to Jace.")

    @patch("os.getenv")
    @patch("builtins.print")
    def test_process_directory_cartesia_no_api_key(self, mock_print, mock_getenv):
        from storybuilder.genai.cartesia_client import process_directory_cartesia

        mock_getenv.return_value = None
        process_directory_cartesia("dummy_dir")
        mock_getenv.assert_called_once_with("CARTESIA_API_KEY")
        mock_print.assert_called_with(
            "Error: CARTESIA_API_KEY not found in environment."
        )

    @patch("os.getenv")
    @patch("glob.glob")
    @patch("builtins.print")
    def test_process_directory_cartesia_no_files(
        self, mock_print, mock_glob, mock_getenv
    ):
        from storybuilder.genai.cartesia_client import process_directory_cartesia

        mock_getenv.return_value = "fake_key"
        mock_glob.return_value = []
        process_directory_cartesia("dummy_dir")
        mock_glob.assert_called_once_with("dummy_dir/*-part.md")
        mock_print.assert_called_with("No prompt files found in dummy_dir")

    @patch("os.getenv")
    @patch("glob.glob")
    @patch("os.path.exists")
    @patch("storybuilder.genai.cartesia_client.process_file_cartesia")
    @patch("time.sleep")
    @patch("builtins.print")
    def test_process_directory_cartesia_success_and_skip(
        self, mock_print, mock_sleep, mock_process, mock_exists, mock_glob, mock_getenv
    ):
        from storybuilder.genai.cartesia_client import process_directory_cartesia

        mock_getenv.return_value = "fake_key"
        # Two files found
        mock_glob.return_value = ["dummy_dir/1-part.md", "dummy_dir/2-part.md"]
        # 1-part.md already has a wav, 2-part.md does not
        mock_exists.side_effect = lambda x: x == "dummy_dir/1-part.wav"

        process_directory_cartesia("dummy_dir", rate=22050)

        # Verify process_file_cartesia is only called for the second file
        mock_process.assert_called_once_with(
            "dummy_dir/2-part.md", "dummy_dir/2-part.wav", "fake_key", rate=22050
        )
        # Verify sleep is called once
        mock_sleep.assert_called_once_with(1)
        mock_print.assert_any_call("Skipping 1-part.md, 1-part.wav already exists.")
