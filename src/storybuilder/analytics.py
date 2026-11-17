"""Shared PostHog analytics client for StoryBuilder runtimes."""

import atexit
import logging
import os
import uuid
from pathlib import Path
from typing import Any

from posthog import Posthog

from storybuilder.utils.env import load_env


logger = logging.getLogger(__name__)

_posthog_client: Posthog | None = None
_distinct_id: str | None = None
_shutdown_registered = False


def _missing_config(variable: str) -> None:
	message = (
		f"{variable} variable required by PostHog is missing or un-configured, "
		f"this causes events to be silently missed. This error stops appearing once {variable} is configured"
	)
	if os.getenv("STORYBUILDER_ENV", "development").lower() == "production":
		logger.error(message)
		return
	raise RuntimeError(message)


def initialize_posthog() -> Posthog | None:
	"""Initialize and return the process-wide PostHog client."""
	global _posthog_client, _shutdown_registered
	if _posthog_client is not None:
		return _posthog_client

	load_env()
	project_token = os.getenv("POSTHOG_PROJECT_TOKEN")
	if not project_token:
		_missing_config("POSTHOG_PROJECT_TOKEN")
		return None

	host = os.getenv("POSTHOG_HOST")
	if not host:
		_missing_config("POSTHOG_HOST")
		return None

	_posthog_client = Posthog(
		project_token,
		host=host,
		enable_exception_autocapture=True,
	)
	if not _shutdown_registered:
		atexit.register(shutdown_posthog)
		_shutdown_registered = True
	return _posthog_client


def get_distinct_id() -> str:
	"""Return a stable anonymous ID for this StoryBuilder installation."""
	global _distinct_id
	if _distinct_id is not None:
		return _distinct_id

	configured_id = os.getenv("POSTHOG_DISTINCT_ID")
	if configured_id:
		_distinct_id = configured_id
		return _distinct_id

	id_path = Path.home() / ".storybuilder" / "analytics_id"
	try:
		if id_path.exists():
			_distinct_id = id_path.read_text(encoding="utf-8").strip()
		if not _distinct_id:
			_distinct_id = str(uuid.uuid4())
			id_path.parent.mkdir(parents=True, exist_ok=True)
			id_path.write_text(_distinct_id, encoding="utf-8")
	except OSError:
		_distinct_id = str(uuid.uuid4())
	return _distinct_id


def capture_event(event: str, properties: dict[str, Any] | None = None) -> None:
	"""Capture a product event for the anonymous installation."""
	client = initialize_posthog()
	if client is not None:
		client.capture(event, distinct_id=get_distinct_id(), properties=properties or {})


def capture_exception(exception: BaseException, properties: dict[str, Any] | None = None) -> None:
	"""Capture a handled exception without adding user-entered content."""
	client = initialize_posthog()
	if client is not None:
		client.capture_exception(exception, distinct_id=get_distinct_id(), properties=properties or {})


def shutdown_posthog() -> None:
	"""Flush queued events and stop the shared client."""
	global _posthog_client
	if _posthog_client is not None:
		_posthog_client.shutdown()
		_posthog_client = None
