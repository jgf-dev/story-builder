"""Quick smoke test: invoke the TTS prompt crafter agent with a real story."""

import asyncio
import os
import sys

# Ensure we can import the agent package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from google.genai import types

from storybuilder.agents.tts_prompt_crafter.agent import APP_NAME, SESSION_ID, USER_ID, runner, session_service


async def main():
    # Create session
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

    story_path = "/home/jgf2/git/voice/story-builder/stories/text/the_secret_vacation-1-I.md"
    user_msg = f"Generate TTS prompts for {story_path}"

    print(f"\n{'=' * 60}")
    print(f"USER: {user_msg}")
    print(f"{'=' * 60}\n")

    content = types.Content(
        role="user",
        parts=[types.Part(text=user_msg)],
    )

    final_response = ""
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    print(f"[{event.author}] {part.text[:500]}")
                    final_response = part.text
                elif hasattr(part, "function_call") and part.function_call:
                    print(f"[{event.author}] TOOL CALL: {part.function_call.name}({dict(part.function_call.args) if part.function_call.args else {}})")
                elif hasattr(part, "function_response") and part.function_response:
                    resp_text = str(part.function_response.response)
                    print(f"[{event.author}] TOOL RESPONSE: {resp_text[:300]}...")

    print(f"\n{'=' * 60}")
    print("DONE")
    print(f"{'=' * 60}")

    # Check if output files were created
    output_dir = os.path.join(os.path.dirname(story_path), "output")
    if os.path.isdir(output_dir):
        files = sorted(os.listdir(output_dir))
        print(f"\nOutput directory contents ({output_dir}):")
        for f in files:
            fp = os.path.join(output_dir, f)
            if os.path.isdir(fp):
                subfiles = os.listdir(fp)
                print(f"  📁 {f}/ ({len(subfiles)} files)")
            else:
                size = os.path.getsize(fp)
                print(f"  📄 {f} ({size} bytes)")
    else:
        print(f"\nNo output directory found at {output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
