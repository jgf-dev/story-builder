import os
from pathlib import Path

from dotenv import load_dotenv


_env_loaded = False


def load_env(dotenv_path: Path | None = None) -> None:
	"""
	Load environment variables from .env file.
	Called once at startup; subsequent calls are no-ops.

	Args:
	    dotenv_path: Optional path to .env file. Defaults to project root.
	"""
	global _env_loaded
	if _env_loaded:
		return

	if dotenv_path is None:
		dotenv_path = Path.cwd() / ".env"

	load_dotenv(dotenv_path=dotenv_path)
	_env_loaded = True


def get_api_key(name: str, required: bool = True) -> str | None:
	"""
	Get an API key from environment variables.

	Args:
	    name: Environment variable name (e.g., "GEMINI_API_KEY", "CARTESIA_API_KEY")
	    required: If True, raises ValueError when key is missing or empty.

	Returns:
	    The API key value, or None if not required.

	Raises:
	    ValueError: If required=True and key is missing or empty.
	"""
	load_env()
	key = os.getenv(name)
	if required and not key:
		raise ValueError(f"Required environment variable '{name}' is not set or empty.")
	return key


def get_optional_api_key(name: str) -> str | None:
	"""Get an optional API key that may be missing."""
	return get_api_key(name, required=False)


def get_stable_api_key(base_name: str) -> str | None:
	"""
	Get a single API key WITHOUT rotation (for TTS use cases).

	TTS requires consistent voice across multiple API calls within a story.
	Using rotation breaks the chain and causes voice mismatch.

	Args:
	    base_name: Base environment variable name (e.g., "GEMINI_API_KEY")

	Returns:
	    The API key value, or None if not set.
	"""
	load_env()
	return os.getenv(base_name)


def get_api_keys_with_rotation(base_name: str) -> list[tuple[str, str]]:
	"""
	Get multiple API keys with numeric suffix rotation (e.g., GEMINI_API_KEY_1, GEMINI_API_KEY_2).

	Use for non-TTS operations where quota rotation is acceptable.
	For TTS generation, use a single key to maintain consistency across calls.

	Args:
	    base_name: Base environment variable name (e.g., "GEMINI_API_KEY")

	Returns:
	    List of (env_var_name, key_value) tuples, starting with the base key.
	"""
	load_env()
	keys = []
	primary = os.getenv(base_name)
	if primary:
		keys.append((base_name, primary))

	idx = 1
	while True:
		key = os.getenv(f"{base_name}_{idx}")
		if key:
			keys.append((f"{base_name}_{idx}", key))
			idx += 1
		else:
			break
	return keys
