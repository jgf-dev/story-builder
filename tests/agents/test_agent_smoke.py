import asyncio
import os
import unittest
from pathlib import Path
from types import SimpleNamespace

from storybuilder.utils.env import load_env
from google.genai import types

from tests.helpers_external_fakes import fake_run_async, live_api_enabled


class TestAgentSmoke(unittest.IsolatedAsyncioTestCase):
    async def test_agent_smoke(self):
        project_root = Path(__file__).resolve().parents[2]
        load_env(project_root / ".env")

        if live_api_enabled():
            await self._live_agent_smoke(project_root)
            return

        # Default unit path: never import the real ADK agent module (import-time
        # Vertex / memory / runner construction). Drive the same assertion loop
        # against an in-process runner double.
        story_path = str(
            project_root / "stories" / "text" / "the_secret_vacation-1-I.md"
        )
        user_msg = f"Generate TTS prompts for {story_path}"
        content = types.Content(
            role="user",
            parts=[types.Part(text=user_msg)],
        )

        USER_ID = "unit-test-user"
        SESSION_ID = "unit-test-session"
        runner = SimpleNamespace(run_async=fake_run_async)

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

        final_response = await asyncio.wait_for(run_agent(), timeout=5.0)
        self.assertGreater(len(final_response), 0)

    async def _live_agent_smoke(self, project_root: Path):
        """Opt-in real ADK multi-agent run (STORYBUILDER_LIVE_API=1)."""
        if not os.getenv("GEMINI_API_KEY") and not os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS"
        ):
            self.skipTest("Vertex AI credentials / Gemini API key not configured")

        from storybuilder.agents.tts_prompt_crafter.agent import (
            APP_NAME,
            SESSION_ID,
            USER_ID,
            runner,
            session_service,
        )

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
