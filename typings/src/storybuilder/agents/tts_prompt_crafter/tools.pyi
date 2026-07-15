import glob
import os
import pathlib
import sys


def read_story(story_path: str) -> str: ...


def list_stories(directory: str | None = None) -> str: ...


def write_scene_file(story_path: str, filename: str, content: str) -> str: ...


def split_scene_files(story_path: str) -> str: ...
