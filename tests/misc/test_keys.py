import os
import unittest
from pathlib import Path

from dotenv import load_dotenv
from google import genai


class TestKeys(unittest.TestCase):
    def test_vertex_ai_client(self):
        project_root = Path(__file__).resolve().parents[2]
        load_dotenv(project_root / ".env")

        if not os.getenv("GEMINI_API_KEY") and not os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS"
        ):
            self.skipTest("Vertex AI credentials / Gemini API key not configured")

        try:
            client = genai.Client(
                vertexai=True, project="storage-499607", location="us-central1"
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents="Say hello!",
            )
            self.assertIsNotNone(response.text)
            self.assertGreater(len(response.text), 0)
        except Exception as e:
            if (
                "quota" in str(e).lower()
                or "permission" in str(e).lower()
                or "unauthenticated" in str(e).lower()
            ):
                self.skipTest(f"Skipped due to API/auth issue: {e}")
            else:
                self.fail(f"Vertex AI Client test failed: {e}")

        if __name__ == "__main__":
            unittest.main()
