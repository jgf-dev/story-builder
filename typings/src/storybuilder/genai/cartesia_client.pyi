from _typeshed import Incomplete

import argparse
import glob
import os
import pathlib
import re
import time
import wave
import requests
from dotenv import load_dotenv

VOICE_MAP: dict[str, str]
NAME_FALLBACK_MAP: dict[str, str]


def wave_file(filename: Incomplete, pcm: Incomplete, channels: Incomplete = 1, rate: Incomplete = 24000, sample_width: Incomplete = 2) -> None: ...


def parse_speech_config_cartesia(markdown_content: str) -> Incomplete: ...


def parse_transcript_segments(markdown_content: str, speaker_to_voice_id: Incomplete, default_voice_id: Incomplete) -> list[tuple[str | None, str]]: ...


def generate_segment_audio(api_key: Incomplete, text: str, voice_id: str | None, rate: Incomplete = 24000) -> bytes | Any: ...


def process_file_cartesia(md_file: str, wav_file: str, api_key: str, rate: Incomplete = 24000) -> None: ...


def process_directory_cartesia(directory: Incomplete, rate: Incomplete = 24000) -> None: ...
