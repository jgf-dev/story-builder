from _typeshed import Incomplete

from google.genai.client import Client
import argparse
import base64
import glob
import os
import pathlib
import re
import time
import wave
from storybuilder.utils.env import load_env
from google import genai


def wave_file_writer(filename: Incomplete, pcm: bytes, channels: Incomplete = 1, rate: Incomplete = 24000, sample_width: Incomplete = 2) -> None: ...


def parse_speech_config(markdown_content: str) -> Incomplete: ...


def get_gemini_api_keys() -> list[tuple[str, str]]: ...


def process_file(md_file: str, wav_file: str, previous_id: Incomplete, api_state: dict[str, Client | int | list[tuple[str, str]]]) -> Incomplete: ...


def process_directory(directory: Incomplete) -> None: ...


def main() -> None: ...
