import os
import pathlib
import re
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in environment.")
    sys.exit(1)

client = genai.Client(api_key=api_key)

PROMPT_INSTRUCTION = (
    "You are an expert audio director. Rewrite the provided TTS prompt text to fix the following issues:\n"
    "1) Add quotation marks (`\"`) around all spoken dialogue to help the TTS model's inflection.\n"
    "2) Ensure dialogue and narration are strictly on separate lines, starting with the character prefix. "
    "If a line currently contains both, split it.\n"
    "3) If Jace's Director's Notes are present, update his style to: 'Jace (Voice: Algenib): 27-year-old. "
    "Masculine, deep. Casual, natural, and grounded. Do not be overly intense or dramatic.'\n"
    "4) In the Pace/Style section, append: 'Maintain a steady, consistent volume and tone throughout.'\n"
    "5) Output the exact same markdown structure, only fixing the text. Do not add any conversational text "
    "or markdown code block markers around the output (like ```markdown), just output the raw markdown text.\n"
)


def extract_markdown_block(content: str) -> str:
    content = content.strip()
    # Match ```markdown ... ``` or ``` ... ```
    match = re.match(
        r"^```(?:markdown)?\s*\n(.*?)\n```$",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()
    # Match any generic block at start and end
    match_any = re.match(r"^```[a-zA-Z0-9_-]*\s*\n(.*?)\n```$", content, re.DOTALL)
    if match_any:
        return match_any.group(1).strip()
    # Fallback to older cleanup if not matching the full block structure perfectly
    if content.startswith("```"):
        lines = content.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return content


def fix_prompts(directory: str) -> None:
    dir_path = pathlib.Path(directory)
    files = sorted([str(p) for p in dir_path.glob("*-part.md")])
    if not files:
        print(f"No prompt files found in {directory}")
        return

    print(f"Found {len(files)} prompt files to process.")
    for md_file in files:
        path = pathlib.Path(md_file)
        content = path.read_text(encoding="utf-8")

        # Skip if already fixed (contains quotes in the transcript)
        if '"' in content.split("#### TRANSCRIPT")[-1]:
            continue

        print(f"Fixing {path.name}...")

        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=f"{PROMPT_INSTRUCTION}\n\nHere is the prompt file content:\n\n{content}",
                config=types.GenerateContentConfig(
                    safety_settings=[
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                            threshold=types.HarmBlockThreshold.BLOCK_NONE,
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                            threshold=types.HarmBlockThreshold.BLOCK_NONE,
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                            threshold=types.HarmBlockThreshold.BLOCK_NONE,
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                            threshold=types.HarmBlockThreshold.BLOCK_NONE,
                        ),
                    ],
                ),
            )
            fixed_content = extract_markdown_block(response.text)

            path.write_text(fixed_content, encoding="utf-8")

            print("  Fixed and saved.")
        except Exception as e:  # noqa: BLE001
            print(f"  Error processing {path.name}: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fix TTS prompt files.")
    parser.add_argument(
        "--dir",
        default="stories/the_secret_vacation_prompts",
        help="Directory containing the *-part.md files",
    )
    args = parser.parse_args()
    fix_prompts(args.dir)
