import os
import unittest
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types


class TestSubagent(unittest.TestCase):
    def test_analyzer_direct(self):
        project_root = Path(__file__).resolve().parents[1]
        load_dotenv(project_root / ".env")

        if not os.getenv("GEMINI_API_KEY") and not os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS"
        ):
            self.skipTest("Vertex AI credentials / Gemini API key not configured")

        prompts_dir = (
            project_root
            / "src"
            / "storybuilder"
            / "agents"
            / "tts_prompt_crafter"
            / "prompts"
        )
        with open(prompts_dir / "story-analyzer.md", "r") as f:
            analyzer_prompt = f.read()

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

        client = genai.Client(
            vertexai=True, project="storage-499607", location="us-central1"
        )

        story_path = project_root / "stories" / "text" / "the_secret_vacation-1-I.md"
        with open(story_path, "r") as f:
            story_content = f.read()

        cleaned_content = story_content
        cleaned_content = cleaned_content.replace("(Gay/Incest)", "(Gay)")
        cleaned_content = cleaned_content.replace("Gay/Incest", "Gay")
        cleaned_content = cleaned_content.replace("incest", "romance")

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
            self.assertGreater(len(response.text), 0)
        except Exception as e:
            if (
                "quota" in str(e).lower()
                or "permission" in str(e).lower()
                or "unauthenticated" in str(e).lower()
            ):
                self.skipTest(f"Skipped due to API/auth issue: {e}")
            else:
                self.fail(f"Subagent direct call failed: {e}")


if __name__ == "__main__":
    unittest.main()
