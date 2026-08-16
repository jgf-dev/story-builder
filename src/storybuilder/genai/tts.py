"""Console entrypoint for Gemini TTS generation.

Installed as ``genai-tts`` via ``[project.scripts]`` in pyproject.toml.
"""

from storybuilder.genai.client import main, process_directory

__all__ = ["main", "process_directory"]


if __name__ == "__main__":
	main()
