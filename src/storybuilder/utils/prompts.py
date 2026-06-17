import os

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "../../prompts")
STORIES_DIR = os.path.join(os.path.dirname(__file__), "../../stories")


def get_prompt(name: str) -> str:
    """Reads a prompt from the prompts/ directory."""
    path = os.path.join(PROMPTS_DIR, f"{name}.md")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Prompt '{name}' not found at {path}")
    with open(path, "r") as f:
        return f.read()


def get_story(name: str) -> str:
    """Reads a story from the stories/ directory."""
    path = os.path.join(STORIES_DIR, f"{name}.md")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Story '{name}' not found at {path}")
    with open(path, "r") as f:
        return f.read()

