import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Explicitly load dotenv
dotenv_path = "/home/jgf2/git/voice/story-builder/.env"
load_dotenv(dotenv_path)

# Load the real story-analyzer prompt
prompts_dir = "/home/jgf2/git/voice/story-builder/src/storybuilder/agents/tts_prompt_crafter/prompts"
with open(os.path.join(prompts_dir, "story-analyzer.md"), "r") as f:
    analyzer_prompt = f.read()

# Safety settings as defined in agent.py
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


def main():
    client = genai.Client(vertexai=True, project="storage-499607", location="us-central1")

    story_path = "/home/jgf2/git/voice/story-builder/stories/text/the_secret_vacation-1-I.md"
    with open(story_path, "r") as f:
        story_content = f.read()

    # Strip metadata header and replace "Incest" / "Straight Brother" references
    cleaned_content = story_content
    cleaned_content = cleaned_content.replace("(Gay/Incest)", "(Gay)")
    cleaned_content = cleaned_content.replace("Gay/Incest", "Gay")
    cleaned_content = cleaned_content.replace("incest", "romance")

    print("Sending cleaned request directly with real prompt...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=cleaned_content,
            config=types.GenerateContentConfig(
                safety_settings=safety_settings,
                system_instruction=analyzer_prompt,
            ),
        )
        print("API Call finished.")
        print(f"Prompt Feedback: {response.prompt_feedback}")
        if response.candidates:
            candidate = response.candidates[0]
            print(f"Finish Reason: {candidate.finish_reason}")
            if candidate.content and candidate.content.parts:
                print(f"Response text length: {len(response.text)}")
                print(f"Response text: {response.text[:500]}...")
            else:
                print("Candidate has no content or parts.")
        else:
            print("Response has no candidates.")
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
