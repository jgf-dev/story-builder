import logging
import sys
from pathlib import Path
from typing import Optional

DEFAULT_FORMAT: Literal['%(asctime)s - %(levelname)s - %(name)s - %(message)s'] = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
SIMPLE_FORMAT: Literal['%(message)s'] = "%(message)s"


def configure_logging(level: int = ..., log_file: Optional[Path] = None, format_string: str = ..., force: bool = False) -> None: ...


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger: ...


def set_library_log_levels(levels: Optional[dict[str, int]] = None) -> None: ...
