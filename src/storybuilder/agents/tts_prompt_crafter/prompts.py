import os
import pathlib


PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
STORIES_DIR = os.getenv("STORIES_TEXT")


def get_prompt(name: str) -> str:
    """Reads a prompt from the prompts/ directory."""
    path = os.path.join(PROMPTS_DIR, f"{name}.md")
    if not pathlib.Path(path).exists():
        raise FileNotFoundError(f"Prompt '{name}' not found at {path}")
    with pathlib.Path(path).open() as f:
        return f.read()


def get_story(name: str) -> str:
    """Reads a story from the stories/ directory."""
    path = os.path.join(STORIES_DIR, f"{name}.md")
    if not pathlib.Path(path).exists():
        raise FileNotFoundError(f"Story '{name}' not found at {path}")
    with pathlib.Path(path).open() as f:
        return f.read()
