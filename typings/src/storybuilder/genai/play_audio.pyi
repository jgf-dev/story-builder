import argparse
import pathlib
import re
import subprocess
import sys


def natural_sort_key(s: str) -> list[object]: ...


def get_audio_player() -> list[str]: ...


def play_sequence(directory: str) -> None: ...
