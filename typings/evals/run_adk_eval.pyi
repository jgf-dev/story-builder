import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

logger: Logger
PROJECT_ROOT: Path
TTS_AGENT_DIR: Path
CARTESIA_AGENT_DIR: Path


def discover_eval_sets(agent_dir: Path) -> list[Path]: ...


def load_eval_set(eval_set_path: Path) -> dict: ...


def print_eval_set_summary(eval_set: dict) -> None: ...


def run_eval_via_adk(eval_set_path: Path, verbose: bool = False) -> dict: ...


def validate_eval_set_structure(eval_set: dict, file_path: str | None = None) -> list[str]: ...


def main() -> None: ...
