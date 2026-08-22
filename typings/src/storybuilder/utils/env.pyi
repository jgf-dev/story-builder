import os
from pathlib import Path
from dotenv import load_dotenv


def load_env(dotenv_path: Path | None = None) -> None: ...


def get_api_key(name: str, required: bool = True) -> str | None: ...


def get_optional_api_key(name: str) -> str | None: ...


def get_stable_api_key(base_name: str) -> str | None: ...


def get_api_keys_with_rotation(base_name: str) -> list[tuple[str, str]]: ...
