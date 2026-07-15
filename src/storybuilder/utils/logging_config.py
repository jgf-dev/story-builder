import logging
import sys
from pathlib import Path
from typing import Optional


DEFAULT_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
SIMPLE_FORMAT = "%(message)s"

_configured = False


def configure_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    format_string: str = DEFAULT_FORMAT,
    force: bool = False,
) -> None:
    """
    Configure logging for the application.

    Called once at startup; subsequent calls are no-ops unless force=True.

    Args:
        level: Logging level (default: INFO)
        log_file: Optional file path to write logs to
        format_string: Log format string
        force: Force reconfiguration even if already configured
    """
    global _configured
    if _configured and not force:
        return

    handlers: list[logging.Handler] = []

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(format_string))
    handlers.append(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(format_string))
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=handlers,
        force=True,
    )

    _configured = True


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a logger with the given name.

    Args:
        name: Logger name (typically __name__)
        level: Optional level override for this logger

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level)
    return logger


def set_library_log_levels(levels: Optional[dict[str, int]] = None) -> None:
    """
    Set log levels for noisy third-party libraries.

    Args:
        levels: Dict of logger name -> level. Defaults to common noisy libraries.
    """
    if levels is None:
        levels = {
            "urllib3": logging.WARNING,
            "requests": logging.WARNING,
            "httpx": logging.WARNING,
            "httpcore": logging.WARNING,
            "boto3": logging.WARNING,
            "botocore": logging.WARNING,
            "google.genai": logging.WARNING,
            "google.adk": logging.WARNING,
            "opentelemetry": logging.WARNING,
        }

    for logger_name, level in levels.items():
        logging.getLogger(logger_name).setLevel(level)
