"""Centralized utility for environment variable loading."""

import os
import pathlib

from dotenv import load_dotenv


def load_env(env_path: str | None = None) -> None:
    """Loads environment variables from a .env file.

    Args:
        env_path: Optional path to the .env file. If not provided,
            it will attempt to find a .env file in the standard locations.
    """
    if env_path:
        load_dotenv(env_path)
    else:
        # Default resolution for common cases
        default_path = pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "..", "..", "..", ".env")).resolve()
        load_dotenv(default_path)
