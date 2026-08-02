import glob
import os
import pathlib
import re

from storybuilder.utils.env import load_env
from google import genai


load_env()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in environment.")
    exit(1)

client = genai.Client(api_key=api_key)

PROMPT_INSTRUCTION = """
You are an expert audio director. Rewrite the provided TTS prompt text to fix the following issues:
1) Add quotation marks (`"`) around all spoken dialogue to help the TTS model's inflection.
2) Ensure dialogue and narration are strictly on separate lines, starting with the character prefix. If a line currently contains both, split it.
3) If Jace's Director's Notes are present, update his style to: 'Jace (Voice: Algenib): 27-year-old. Masculine, deep. Casual, natural, and grounded. Do not be overly intense or dramatic.'
4) In the Pace/Style section, append: 'Maintain a steady, consistent volume and tone throughout.'
5) Output the exact same markdown structure, only fixing the text. Do not add any conversational text or markdown code block markers around the output (like ```markdown), just output the raw markdown text.
"""


def extract_markdown_block(content: str) -> str:
    content = content.strip()
    if not content.startswith("```"):
        return content

    lines = content.split("\n")
    # Strict matching block check
    if content.endswith("```") and lines[-1].strip() == "```" and re.match(r"^```[a-zA-Z0-9_-]*$", lines[0].strip()):
        return "\n".join(lines[1:-1]).strip()

    # Fallback to older cleanup
    cleaned_lines = lines[1:]
    if cleaned_lines and cleaned_lines[-1].strip() == "```":
        cleaned_lines = cleaned_lines[:-1]
    return "\n".join(cleaned_lines).strip()


def fix_prompts(directory) -> None:
    files = sorted(glob.glob(os.path.join(directory, "*-part.md")))
    if not files:
        print(f"No prompt files found in {directory}")
        return

    print(f"Found {len(files)} prompt files to process.")
    for md_file in files:
        print(f"Fixing {os.path.basename(md_file)}...")
        content = pathlib.Path(md_file).read_text()

        try:
            interaction = client.interactions.create(
                model="gemini-3.5-flash",
                input=f"{PROMPT_INSTRUCTION}\n\nHere is the prompt file content:\n\n{content}",
            )
            fixed_content = extract_markdown_block(interaction.output_text)

            pathlib.Path(md_file).write_text(fixed_content)

            print("  Fixed and saved.")
        except Exception as e:
            print(f"  Error processing {os.path.basename(md_file)}: {e}")


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
