from _typeshed import Incomplete

import json
from pathlib import Path
import pytest
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner

PROJECT_ROOT: Path
DATASETS_DIR: Path


@pytest.fixture(scope="session")
def project_root() -> Path: ...


@pytest.fixture(scope="session")
def datasets_dir() -> Path: ...


@pytest.fixture
def load_jsonl(request: Incomplete) -> Incomplete: ...


@pytest.fixture(scope="session")
def tts_agent() -> LlmAgent: ...


@pytest.fixture(scope="session")
def tts_runner(tts_agent: Incomplete) -> Runner: ...


@pytest.fixture
def adk_events(tts_runner: Incomplete) -> Incomplete: ...
