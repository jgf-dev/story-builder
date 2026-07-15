"""Shared pytest fixtures for zero-network unit tests.

Fakes replace Gemini text-gen, ADK runner, and TTS process_file entry points.
Production code under src/ is not patched at import for the whole suite;
individual tests request fixtures or use helpers from helpers_external_fakes.
"""

from __future__ import annotations

import pytest

from tests.helpers_external_fakes import (
    fake_process_file_factory,
    live_api_enabled,
    make_fake_genai_client,
    make_generate_content_response,
)


@pytest.fixture
def live_api() -> bool:
    """Whether STORYBUILDER_LIVE_API is set (opt-in real backends)."""
    return live_api_enabled()


@pytest.fixture
def fake_genai_client():
    """In-process google.genai.Client double (no network)."""
    return make_fake_genai_client()


@pytest.fixture
def fake_generate_content_response():
    return make_generate_content_response()


@pytest.fixture
def fake_tts_process_file():
    """Deterministic storybuilder.genai.client.process_file replacement."""
    return fake_process_file_factory()


@pytest.fixture
def mock_genai_client(monkeypatch, fake_genai_client):
    """Patch google.genai.Client (and google.genai if imported as package)."""

    def _client_factory(*_args, **_kwargs):
        return fake_genai_client

    monkeypatch.setattr("google.genai.Client", _client_factory)
    try:
        monkeypatch.setattr("google.genai.client.Client", _client_factory)
    except (AttributeError, ImportError, ModuleNotFoundError):
        # Optional alternate import path may not exist in all environments.
        pass
    return fake_genai_client


@pytest.fixture
def mock_gemini_tts_process_file(monkeypatch, fake_tts_process_file):
    """Patch storybuilder.genai.client.process_file to write a tiny WAV."""
    monkeypatch.setattr(
        "storybuilder.genai.client.process_file",
        fake_tts_process_file,
    )
    return fake_tts_process_file


@pytest.fixture(autouse=True)
def clean_globals():
    """Autouse fixture to reset global states (database connections, scraping caches) before and after each test."""
    # Reset seen_folders
    try:
        from storybuilder.downloader.scraper import seen_folders
    except ImportError:
        seen_folders = None
    if seen_folders is not None:
        seen_folders.clear()

    # Close DB
    try:
        from storybuilder.downloader.db import close_db
    except ImportError:
        close_db = None
    if close_db is not None:
        close_db()

    yield

    # Cleanup after test
    try:
        from storybuilder.downloader.scraper import seen_folders
    except ImportError:
        seen_folders = None
    if seen_folders is not None:
        seen_folders.clear()

    try:
        from storybuilder.downloader.db import close_db
    except ImportError:
        close_db = None
    if close_db is not None:
        close_db()
