import os
import pathlib
import re
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

api_key: str | None
client: Client
PROMPT_INSTRUCTION: Literal['You are an expert audio director. Rewrite the provided TTS prompt text to fix the following issues:\n1) Add quotation marks (`"`) around all spoken dialogue to help the TTS model\'s inflection.\n2) Ensure dialogue and narration are strictly on separate lines, starting with the character prefix. If a line currently contains both, split it.\n3) If Jace\'s Director\'s Notes are present, update his style to: \'Jace (Voice: Algenib): 27-year-old. Masculine, deep. Casual, natural, and grounded. Do not be overly intense or dramatic.\'\n4) In the Pace/Style section, append: \'Maintain a steady, consistent volume and tone throughout.\'\n5) Output the exact same markdown structure, only fixing the text. Do not add any conversational text or markdown code block markers around the output (like ```markdown), just output the raw markdown text.\n'] = "You are an expert audio director. Rewrite the provided TTS prompt text to fix the following issues:\n"
    "1) Add quotation marks (`\"`) around all spoken dialogue to help the TTS model's inflection.\n"
    "2) Ensure dialogue and narration are strictly on separate lines, starting with the character prefix. "
    "If a line currently contains both, split it.\n"
    "3) If Jace's Director's Notes are present, update his style to: 'Jace (Voice: Algenib): 27-year-old. "
    "Masculine, deep. Casual, natural, and grounded. Do not be overly intense or dramatic.'\n"
    "4) In the Pace/Style section, append: 'Maintain a steady, consistent volume and tone throughout.'\n"
    "5) Output the exact same markdown structure, only fixing the text. Do not add any conversational text "
    "or markdown code block markers around the output (like ```markdown), just output the raw markdown text.\n"


def extract_markdown_block(content: str) -> str: ...


def fix_prompts(directory: str) -> None: ...
