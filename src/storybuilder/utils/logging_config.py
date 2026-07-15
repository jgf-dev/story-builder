"""Centralized utility for standardized logging setup."""

import logging
import sys


_logging_configured = False


def configure_logging(level: int = logging.INFO) -> None:
    """Configures the standard logging format for the application.

    Uses memoization to ensure logging is only configured once.

    Args:
        level: The logging level to set (default: logging.INFO).
    """
    global _logging_configured
    if _logging_configured:
        return

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    _logging_configured = True
