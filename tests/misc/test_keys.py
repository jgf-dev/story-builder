import os
import unittest
from pathlib import Path
from unittest.mock import patch

from storybuilder.utils.env import load_env
from tests.helpers_external_fakes import live_api_enabled
from tests.helpers_external_fakes import make_fake_genai_client


class TestKeys(unittest.TestCase):
    def test_vertex_ai_client(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        load_env(project_root / ".env")

        if live_api_enabled():
            self._live_vertex_ai_client()
            return

        # Default unit path: deterministic Client double — no network.
        fake_client = make_fake_genai_client(text="Hello from unit mock")
        with patch("google.genai.Client", return_value=fake_client) as mock_ctor:
            from google import genai

            client = genai.Client(vertexai=True, project="storage-499607", location="us-central1")
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents="Say hello!",
            )
            self.assertIsNotNone(response.text)
            self.assertGreater(len(response.text), 0)
            mock_ctor.assert_called()
            client.models.generate_content.assert_called_once()

    def _live_vertex_ai_client(self) -> None:
        """Opt-in real Vertex probe (STORYBUILDER_LIVE_API=1)."""
        from google import genai

        if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            self.skipTest("Vertex AI credentials / Gemini API key not configured")

        try:
            client = genai.Client(vertexai=True, project="storage-499607", location="us-central1")
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents="Say hello!",
            )
            self.assertIsNotNone(response.text)
            self.assertGreater(len(response.text), 0)
        except Exception as e:
            if "quota" in str(e).lower() or "permission" in str(e).lower() or "unauthenticated" in str(e).lower():
                self.skipTest(f"Skipped due to API/auth issue: {e}")
            else:
                self.fail(f"Vertex AI Client test failed: {e}")


if __name__ == "__main__":
    unittest.main()
