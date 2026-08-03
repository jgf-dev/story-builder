import pathlib
import tempfile
import unittest
<<<<<<< HEAD

from storybuilder.genai.cartesia_client import NAME_FALLBACK_MAP
from storybuilder.genai.cartesia_client import VOICE_MAP
from storybuilder.genai.cartesia_client import parse_speech_config_cartesia
from storybuilder.genai.cartesia_client import parse_transcript_segments
=======
import wave

from storybuilder.genai.cartesia_client import (
	NAME_FALLBACK_MAP,
	VOICE_MAP,
	parse_speech_config_cartesia,
	parse_transcript_segments,
	wave_file,
)
>>>>>>> origin/main


class TestCartesiaClient(unittest.TestCase):
	def test_wave_file(self) -> None:
		with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
			tmp_name = tmp.name

		try:
			pcm_data = b"\x00\x01\x02\x03\x04\x05\x06\x07"
			wave_file(tmp_name, pcm_data, channels=2, rate=44100, sample_width=2)

			with wave.open(tmp_name, "rb") as wf:
				assert wf.getnchannels() == 2
				assert wf.getsampwidth() == 2
				assert wf.getframerate() == 44100
				assert wf.readframes(1024) == pcm_data
		finally:
			pathlib.Path(tmp_name).unlink()

	def test_parse_speech_config_cartesia(self) -> None:
		markdown_content = """
        ### DIRECTOR'S NOTES
        Style:
        - Jace (Voice: Algenib): 27-year-old.
        - Levi (Voice: Kyle): 20-year-old.
        - Kerry (Voice: 6ccbfb76-1fc6-48f7-b71d-91ac6298247b): Custom UUID.
        """
		config = parse_speech_config_cartesia(markdown_content)

		assert config["Jace"] == VOICE_MAP["algenib"]
		assert config["Levi"] == VOICE_MAP["kyle"]
		assert config["Kerry"] == "6ccbfb76-1fc6-48f7-b71d-91ac6298247b"

	def test_parse_transcript_segments(self) -> None:
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

		# Levi has no explicit definition in speaker_to_voice_id,
		# should fallback to NAME_FALLBACK_MAP or default_voice_id
		segments = parse_transcript_segments(
			markdown_content,
			speaker_to_voice_id,
			default_voice_id="default-voice-uuid",
		)

		# Check segment grouping (the two Jace lines are adjacent and should be grouped together!)
		assert len(segments) == 4

		# Segment 1: Jace lines grouped
		assert segments[0][0] == "jace-voice-uuid"
		assert segments[0][1] == "Hello, my name is Jace. And this is my second line."

		# Segment 2: Narrator
		assert segments[1][0] == "narrator-voice-uuid"
		assert segments[1][1] == "This is the narrator speaking here."

		# Segment 3: Levi fallback
		assert segments[2][0] == NAME_FALLBACK_MAP["levi"]
		assert segments[2][1] == "Hey, Levi here!"

		# Segment 4: Jace
		assert segments[3][0] == "jace-voice-uuid"
		assert segments[3][1] == "Back to Jace."


if __name__ == "__main__":
	unittest.main()
