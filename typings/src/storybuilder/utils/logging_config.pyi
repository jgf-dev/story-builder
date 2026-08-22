import logging
import sys
from pathlib import Path

DEFAULT_FORMAT: Literal['%(asctime)s - %(levelname)s - %(name)s - %(message)s'] = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
SIMPLE_FORMAT: Literal['%(message)s'] = "%(message)s"


def configure_logging(level: int = ..., log_file: Path | None = None, format_string: str = ..., force: bool = False) -> None: ...


def get_logger(name: str, level: int | None = None) -> logging.Logger: ...


def set_library_log_levels(levels: dict[str, int] | None = None) -> None: ...
