"""Shared pytest fixtures for ADK agent evaluations.

These fixtures provide reusable test infrastructure for evaluating
Google ADK agents used in the story-builder project.

Fixtures:
    tts_agent: Returns the TTS Prompt Crafter ADK root agent.
    tts_runner: Returns an ADK Runner configured for the TTS agent.
    evaluation_datasets: Path to the evaluation datasets directory.
"""

import json
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parent.parent
DATASETS_DIR = PROJECT_ROOT / "evals" / "datasets"


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def datasets_dir() -> Path:
    """Return the evaluation datasets directory."""
    return DATASETS_DIR


@pytest.fixture
def load_jsonl(request):
    """Load a JSONL dataset file by name.

    Usage:
        def test_my_eval(load_jsonl):
            data = load_jsonl("tts_greetings.jsonl")
    """

    def _load(filename: str) -> list[dict]:
        filepath = DATASETS_DIR / filename
        if not filepath.exists():
            pytest.skip(f"Dataset file not found: {filepath}")
        records = []
        with Path(filepath).open() as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

    return _load


@pytest.fixture(scope="session")
def tts_agent():
    """Return the TTS Prompt Crafter root agent.

    The agent is a Google ADK LlmAgent with sub-agents for story
    analysis and scene writing, plus tools for file I/O.
    """
    try:
        from storybuilder.agents.tts_prompt_crafter.agent import root_agent

        return root_agent
    except ImportError:
        pytest.skip("TTS Prompt Crafter agent module not available")


@pytest.fixture(scope="session")
def tts_runner(tts_agent):
    """Return an ADK Runner configured for the TTS agent.

    Uses InMemorySessionService for stateless evaluation runs
    so each test starts with a clean session.
    """
    try:
        from google.adk.artifacts import InMemoryArtifactService
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService

        session_service = InMemorySessionService()
        artifact_service = InMemoryArtifactService()

        runner = Runner(
            agent=tts_agent,
            app_name="tts_prompt_crafter_eval",
            session_service=session_service,
            artifact_service=artifact_service,
        )
        return runner
    except ImportError as e:
        pytest.skip(f"ADK runner creation failed: {e}")


@pytest.fixture
def adk_events(tts_runner):
    """Fixture that runs a query through the ADK runner and returns events.

    Usage:
        def test_my_query(adk_events):
            events = adk_events("Tell me about your capabilities")
            last_event = events[-1]
            assert last_event.content is not None
    """
    import asyncio

    # Store runner reference for the inner function
    runner = tts_runner

    # Use a fresh, per-call InMemorySessionService so each test starts
    # with a clean session. Also enable ``auto_create_session`` so the
    # runner auto-creates a session on first call instead of raising
    # ``SessionNotFoundError``.
    runner.auto_create_session = True

    async def _run_query(query: str) -> list:
        from google.genai import types as genai_types

        # ADK's ``run_async`` expects ``new_message`` to be a
        # ``google.genai.types.Content`` (with at least one Part),
        # not a raw string. Wrap the query accordingly.
        new_message = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=query)],
        )

        events = []
        async for event in runner.run_async(
            user_id="eval_user",
            session_id=f"eval_session_{id(query)}",
            new_message=new_message,
        ):
            events.append(event)
        return events

    def _run_sync(query: str) -> list:
        return asyncio.run(_run_query(query))

    return _run_sync
