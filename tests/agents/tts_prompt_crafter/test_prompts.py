from pathlib import Path
from unittest.mock import patch

import pytest

from storybuilder.agents.tts_prompt_crafter.prompts import get_prompt, get_story


def test_get_prompt_success(tmp_path: Path) -> None:
    prompt_file = tmp_path / "test_prompt.md"
    prompt_file.write_text("Hello, prompt!")

    with patch("storybuilder.agents.tts_prompt_crafter.prompts.PROMPTS_DIR", str(tmp_path)):
        result = get_prompt("test_prompt")
        # ruff: ignore[assert]
        assert result == "Hello, prompt!"


def test_get_prompt_not_found(tmp_path: Path) -> None:
    with (
        patch("storybuilder.agents.tts_prompt_crafter.prompts.PROMPTS_DIR", str(tmp_path)),
        pytest.raises(FileNotFoundError, match="Prompt 'missing_prompt' not found at"),
    ):
        get_prompt("missing_prompt")


def test_get_story_success(tmp_path: Path) -> None:
    story_file = tmp_path / "test_story.md"
    story_file.write_text("Hello, story!")

    with patch("storybuilder.agents.tts_prompt_crafter.prompts.STORIES_DIR", str(tmp_path)):
        result = get_story("test_story")
        # ruff: ignore[assert]
        assert result == "Hello, story!"


def test_get_story_not_found(tmp_path: Path) -> None:
    with (
        patch("storybuilder.agents.tts_prompt_crafter.prompts.STORIES_DIR", str(tmp_path)),
        pytest.raises(FileNotFoundError, match="Story 'missing_story' not found at"),
    ):
        get_story("missing_story")
