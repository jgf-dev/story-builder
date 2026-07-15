import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


def load_env(dotenv_path: Optional[Path] = None) -> None: ...


def get_api_key(name: str, required: bool = True) -> Optional[str]: ...


def get_optional_api_key(name: str) -> Optional[str]: ...


def get_stable_api_key(base_name: str) -> Optional[str]: ...


def get_api_keys_with_rotation(base_name: str) -> list[tuple[str, str]]: ...
