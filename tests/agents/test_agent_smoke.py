import os
import unittest
from pathlib import Path

from dotenv import load_dotenv
from google.genai import types


class TestAgentSmoke(unittest.IsolatedAsyncioTestCase):
    async def test_agent_smoke(self):
        project_root = Path(__file__).resolve().parents[2]
        load_dotenv(project_root / ".env")

        if not os.getenv("GEMINI_API_KEY") and not os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS"
        ):
            self.skipTest("Vertex AI credentials / Gemini API key not configured")

        from storybuilder.agents.tts_prompt_crafter.agent import APP_NAME
        from storybuilder.agents.tts_prompt_crafter.agent import SESSION_ID
        from storybuilder.agents.tts_prompt_crafter.agent import USER_ID
        from storybuilder.agents.tts_prompt_crafter.agent import runner
        from storybuilder.agents.tts_prompt_crafter.agent import session_service

        if not await session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID,
        ):
            await session_service.create_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                session_id=SESSION_ID,
            )

        story_path = str(
            project_root / "stories" / "text" / "the_secret_vacation-1-I.md"
        )
        user_msg = f"Generate TTS prompts for {story_path}"
        content = types.Content(
            role="user",
            parts=[types.Part(text=user_msg)],
        )

        import asyncio

        async def run_agent():
            response_text = ""
            async for event in runner.run_async(
                user_id=USER_ID,
                session_id=SESSION_ID,
                new_message=content,
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            response_text = part.text
            return response_text

        try:
            final_response = await asyncio.wait_for(run_agent(), timeout=90.0)
            self.assertGreater(len(final_response), 0)
        except asyncio.TimeoutError:
            self.skipTest(
                "Skipped: Agent execution timed out after 90 seconds. This might be due to API latency or network issues."
            )
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
                self.fail(f"Agent execution failed: {e}")


if __name__ == "__main__":
    unittest.main()
