import unittest

from storybuilder.genai.cartesia_client import (
	NAME_FALLBACK_MAP,
	VOICE_MAP,
	parse_speech_config_cartesia,
	parse_transcript_segments,
)


class TestCartesiaClient(unittest.TestCase):
	def test_parse_speech_config_cartesia(self) -> None:
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

		# Levi has no explicit definition in speaker_to_voice_id, should fallback to NAME_FALLBACK_MAP or default_voice_id
		segments = parse_transcript_segments(
			markdown_content, speaker_to_voice_id, default_voice_id="default-voice-uuid"
		)

		# Check segment grouping (the two Jace lines are adjacent and should be grouped together!)
		self.assertEqual(len(segments), 4)

		# Segment 1: Jace lines grouped
		self.assertEqual(segments[0][0], "jace-voice-uuid")
		self.assertEqual(segments[0][1], "Hello, my name is Jace. And this is my second line.")

		# Segment 2: Narrator
		self.assertEqual(segments[1][0], "narrator-voice-uuid")
		self.assertEqual(segments[1][1], "This is the narrator speaking here.")

		# Segment 3: Levi fallback
		self.assertEqual(segments[2][0], NAME_FALLBACK_MAP["levi"])
		self.assertEqual(segments[2][1], "Hey, Levi here!")

		# Segment 4: Jace
		self.assertEqual(segments[3][0], "jace-voice-uuid")
		self.assertEqual(segments[3][1], "Back to Jace.")


if __name__ == "__main__":
	unittest.main()
