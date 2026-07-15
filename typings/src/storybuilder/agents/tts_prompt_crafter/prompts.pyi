import os
import pathlib

PROMPTS_DIR: str
STORIES_DIR: str | None


def get_prompt(name: str) -> str: ...


def get_story(name: str) -> str: ...
