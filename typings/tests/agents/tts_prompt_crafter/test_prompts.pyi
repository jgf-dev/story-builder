from pathlib import Path
from unittest.mock import patch
import pytest
from storybuilder.agents.tts_prompt_crafter.prompts import get_prompt
from storybuilder.agents.tts_prompt_crafter.prompts import get_story


def test_get_prompt_success(tmp_path: Path) -> None: ...


def test_get_prompt_not_found(tmp_path: Path) -> None: ...


def test_get_story_success(tmp_path: Path) -> None: ...


def test_get_story_not_found(tmp_path: Path) -> None: ...
