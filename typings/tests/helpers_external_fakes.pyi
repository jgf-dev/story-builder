from __future__ import annotations
import os
import wave
from types import SimpleNamespace
from typing import Any, AsyncIterator, Callable
from unittest.mock import MagicMock

LIVE_API_ENV: Literal['STORYBUILDER_LIVE_API'] = "STORYBUILDER_LIVE_API"


def live_api_enabled() -> bool: ...


def write_tiny_wav(path: str, *, frames: int = 240) -> None: ...


def make_generate_content_response(text: str = "fake analysis response") -> MagicMock: ...


def make_fake_genai_client(*, text: str = "fake analysis response", generate_content: Callable[..., Any] | None = None) -> MagicMock: ...


def fake_process_file_factory() -> Callable[..., tuple[Any, int, str]]: ...


def make_fake_adk_event(text: str = "Fake TTS prompt craft result") -> SimpleNamespace: ...


async def fake_run_async(**_kwargs: Any) -> AsyncIterator[SimpleNamespace]: ...
