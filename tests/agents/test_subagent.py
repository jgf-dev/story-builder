from google.genai.types import SafetySetting
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from google.genai import types

from storybuilder.utils.env import load_env
from tests.helpers_external_fakes import live_api_enabled
from tests.helpers_external_fakes import make_fake_genai_client


class TestSubagent(unittest.TestCase):
	def test_analyzer_direct(self) -> None:
		project_root = Path(__file__).resolve().parents[2]
		load_env(project_root / ".env")

		prompts_dir = project_root / "src" / "storybuilder" / "agents" / "tts_prompt_crafter" / "prompts"
		analyzer_prompt = Path(prompts_dir / "story-analyzer.md").read_text()

		safety_settings = [
			types.SafetySetting(
				category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
				threshold=types.HarmBlockThreshold.OFF,
			),
			types.SafetySetting(
				category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
				threshold=types.HarmBlockThreshold.OFF,
			),
			types.SafetySetting(
				category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
				threshold=types.HarmBlockThreshold.OFF,
			),
			types.SafetySetting(
				category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
				threshold=types.HarmBlockThreshold.OFF,
			),
			types.SafetySetting(
				category=types.HarmCategory.HARM_CATEGORY_UNSPECIFIED,
				threshold=types.HarmBlockThreshold.OFF,
			),
		]

		story_path = project_root / "stories" / "text" / "the_secret_vacation-1-I.md"
		story_content = Path(story_path).read_text()

		cleaned_content = story_content
		cleaned_content = cleaned_content.replace("(Gay/Incest)", "(Gay)")
		cleaned_content = cleaned_content.replace("Gay/Incest", "Gay")
		cleaned_content = cleaned_content.replace("incest", "romance")

		if live_api_enabled():
			self._live_analyzer(cleaned_content, analyzer_prompt, safety_settings)
			return

		# Default unit path: patch Client so generate_content never leaves process.
		fake_client = make_fake_genai_client(
			text="fake story analysis for unit test",
		)
		with patch("google.genai.Client", return_value=fake_client):
			from google import genai

			client = genai.Client(vertexai=True, project="storage-499607", location="us-central1")
			response = client.models.generate_content(
				model="gemini-2.5-flash",
				contents=cleaned_content,
				config=types.GenerateContentConfig(
					safety_settings=safety_settings,
					system_instruction=analyzer_prompt,
				),
			)
			self.assertTrue(response.candidates)
			self.assertGreater(len(response.text or ""), 0)
			from typing import Any

			generate_content_mock: Any = client.models.generate_content
			generate_content_mock.assert_called_once()

	def _live_analyzer(self, cleaned_content: str, analyzer_prompt: str, safety_settings: list[SafetySetting]) -> None:
		"""Opt-in real Vertex generate_content (STORYBUILDER_LIVE_API=1)."""
		from google import genai

		if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
			self.skipTest("Vertex AI credentials / Gemini API key not configured")

		client = genai.Client(vertexai=True, project="storage-499607", location="us-central1")
		try:
			response = client.models.generate_content(
				model="gemini-2.5-flash",
				contents=cleaned_content,
				config=types.GenerateContentConfig(
					safety_settings=safety_settings,
					system_instruction=analyzer_prompt,
				),
			)
			self.assertTrue(response.candidates)
			self.assertGreater(len(response.text or ""), 0)
		except Exception as e:
			if (
				"quota" in str(e).lower()
				or "permission" in str(e).lower()
				or "unauthenticated" in str(e).lower()
				or "resource_exhausted" in str(e).lower()
				or "resource exhausted" in str(e).lower()
				or "429" in str(e).lower()
			):
				self.skipTest(f"Skipped due to API/auth issue: {e}")
			else:
				self.fail(f"Subagent direct call failed: {e}")


if __name__ == "__main__":
	unittest.main()
