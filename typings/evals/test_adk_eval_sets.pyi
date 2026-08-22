from _typeshed import Incomplete

import json
from pathlib import Path
import pytest

PROJECT_ROOT: Path
TTS_AGENT_DIR: Path
CARTESIA_AGENT_DIR: Path


def discover_eval_sets(agent_dir: Path) -> list[Path]: ...


@pytest.fixture(params=["tts_prompt_crafter", "cartesia_tts_prompt_crafter"])
def agent_dir(request: Incomplete) -> Path: ...


class TestEvalSetDiscovery:
    def test_tts_prompt_crafter_has_evals(self) -> None: ...

    def test_cartesia_agent_has_evals(self) -> None: ...


class TestEvalSetStructure:
    @pytest.mark.parametrize(
		"eval_path",
		discover_eval_sets(TTS_AGENT_DIR) + discover_eval_sets(CARTESIA_AGENT_DIR),
		ids=lambda p: p.parent.name + "/" + p.stem,
	)
    def test_eval_set_structure(self, eval_path: Path) -> None: ...

    def test_all_eval_sets_have_unique_ids(self) -> None: ...


class TestEvalRunViaADK:
    @pytest.mark.slow
    @pytest.mark.parametrize(
		"eval_path",
		discover_eval_sets(TTS_AGENT_DIR),
		ids=lambda p: p.stem,
	)
    def test_run_tts_eval_set(self, eval_path: Path) -> None: ...

    @pytest.mark.slow
    @pytest.mark.skip(reason="Cartesia TTS agent tools not yet implemented")
    def test_run_cartesia_eval_set(self) -> None: ...
