"""Console entrypoint for Gemini TTS generation.

Installed as ``genai-tts`` via ``[project.scripts]`` in pyproject.toml.
"""

from storybuilder.genai.client import main
from storybuilder.genai.client import process_directory


__all__ = ["main", "process_directory"]
from storybuilder.genai.client import main as client_main

def main():
    client_main()


if __name__ == "__main__":
    main()