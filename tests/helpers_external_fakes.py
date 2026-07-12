"""Deterministic in-process fakes for text-gen, ADK agent, and Gemini TTS.

Used by unit tests so the suite never hits real Gemini / Vertex / TTS backends.
Live API paths remain available only when STORYBUILDER_LIVE_API=1 (opt-in).
"""

from __future__ import annotations

import os
import wave
from types import SimpleNamespace
from typing import Any, AsyncIterator, Callable
from unittest.mock import MagicMock


LIVE_API_ENV = "STORYBUILDER_LIVE_API"


def live_api_enabled() -> bool:
    """True only when the operator explicitly opts into real backends."""
    return os.getenv(LIVE_API_ENV, "").strip().lower() in {"1", "true", "yes"}


def write_tiny_wav(path: str, *, frames: int = 240) -> None:
    """Write a minimal valid mono 24 kHz 16-bit PCM WAV (non-empty)."""
    pcm = b"\x00\x00" * frames
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(pcm)


def make_generate_content_response(text: str = "fake analysis response") -> MagicMock:
    """Shape compatible with google.genai generate_content return value."""
    response = MagicMock()
    candidate = MagicMock()
    candidate.content = MagicMock()
    response.candidates = [candidate]
    response.text = text
    return response


def make_fake_genai_client(
    *,
    text: str = "fake analysis response",
    generate_content: Callable[..., Any] | None = None,
) -> MagicMock:
    """Client double: models.generate_content returns fixed text; no network."""
    client = MagicMock(name="FakeGenaiClient")
    if generate_content is None:
        generate_content = MagicMock(
            return_value=make_generate_content_response(text),
        )
    client.models.generate_content = generate_content
    client.interactions.create = MagicMock(
        return_value=SimpleNamespace(
            id="fake-interaction-id",
            output_audio=SimpleNamespace(
                data=None,
                mime_type="audio/pcm;rate=24000",
            ),
        ),
    )
    return client


def fake_process_file_factory() -> Callable[..., tuple[Any, int, str]]:
    """Return a process_file stand-in that writes a tiny WAV and chains ids."""

    counter = {"n": 0}

    def fake_process_file(
        md_file: str,
        wav_file: str,
        client: Any,
        previous_id: str | None,
        api_keys: list,
        current_key_idx: int,
    ) -> tuple[Any, int, str]:
        del md_file, api_keys  # unused; kept for signature parity
        counter["n"] += 1
        write_tiny_wav(wav_file)
        interaction_id = f"fake-interaction-id-{counter['n']}"
        if previous_id:
            # Continuity: still produce a new id while acknowledging previous_id
            interaction_id = f"{previous_id}->n{counter['n']}"
        return client, current_key_idx, interaction_id

    return fake_process_file


def make_fake_adk_event(text: str = "Fake TTS prompt craft result") -> SimpleNamespace:
    """Minimal ADK event with content.parts[*].text for the smoke test loop."""
    part = SimpleNamespace(text=text)
    content = SimpleNamespace(parts=[part])
    return SimpleNamespace(content=content)


async def fake_run_async(**_kwargs: Any) -> AsyncIterator[SimpleNamespace]:
    """Async generator matching runner.run_async usage in the smoke test."""
    yield make_fake_adk_event()
