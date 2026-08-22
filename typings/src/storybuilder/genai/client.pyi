import argparse
import base64
import glob
import logging
import os
import pathlib
import re
import time
import wave
from os import PathLike
from typing import Any
from google import genai
from google.genai.client import Client
from storybuilder.utils.env import load_env

logger: Logger


def wave_file_writer(filename: str | PathLike[Any], pcm: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2) -> None: ...


def parse_speech_config(markdown_content: str) -> list[dict[str, str]]: ...


def get_gemini_api_keys() -> list[tuple[str, str]]: ...


class ApiKeyRotator:
    api_keys: list[tuple[str, str]]
    current_key_idx: int

    def __init__(self, api_keys: list[tuple[str, str]]) -> None: ...

    @property
    def current_key_name(self) -> str: ...

    @property
    def client(self) -> Client: ...

    def rotate(self) -> None: ...

    @property
    def total_keys(self) -> int: ...


def process_file(md_file: str, wav_file: str, previous_id: str | None, rotator: ApiKeyRotator) -> str | None: ...


def process_directory(directory: str | pathlib.Path) -> None: ...


def main() -> None: ...
