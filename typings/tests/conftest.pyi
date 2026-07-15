from _typeshed import Incomplete

from __future__ import annotations
import pytest
from tests.helpers_external_fakes import (
    fake_process_file_factory,
    live_api_enabled,
    make_fake_genai_client,
    make_generate_content_response,
)


@pytest.fixture
def live_api() -> bool: ...


@pytest.fixture
def fake_genai_client() -> Incomplete: ...


@pytest.fixture
def fake_generate_content_response() -> Incomplete: ...


@pytest.fixture
def fake_tts_process_file() -> Incomplete: ...


@pytest.fixture
def mock_genai_client(monkeypatch: Incomplete, fake_genai_client: Incomplete) -> Incomplete: ...


@pytest.fixture
def mock_gemini_tts_process_file(monkeypatch: Incomplete, fake_tts_process_file: Incomplete) -> Incomplete: ...
