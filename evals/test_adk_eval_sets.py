"""Tests that validate and run ADK eval set files.

These tests load .evalset.json files from the agent directories and:
1. Validate their structural integrity (schema correctness)
2. Optionally run them through the ADK evaluation engine

Run with:
    pytest evals/test_adk_eval_sets.py -v
"""

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
TTS_AGENT_DIR = PROJECT_ROOT / "src" / "storybuilder" / "agents" / "tts_prompt_crafter"
CARTESIA_AGENT_DIR = PROJECT_ROOT / "src" / "storybuilder" / "agents" / "cartesia_tts_prompt_crafter"


def discover_eval_sets(agent_dir: Path) -> list[Path]:
	"""Find all .evalset.json files in an agent directory."""
	return sorted(agent_dir.glob("*.evalset.json"))


def _validate_eval_set_structure(data: dict, name: str) -> list[str]:
	"""Validate the structure of an ADK eval set."""
	issues = []

	# Check required top-level fields
	if not data.get("eval_set_id") and not data.get("name"):
		issues.append("Missing 'eval_set_id' and 'name'")

	eval_cases = data.get("eval_cases", [])
	if not eval_cases:
		issues.append("No 'eval_cases' found")

	for i, case in enumerate(eval_cases):
		case_id = case.get("eval_id", f"case_{i}")
		conv = case.get("conversation", [])

		if not case_id:
			issues.append(f"case[{i}]: Missing 'eval_id'")

		if not conv:
			issues.append(f"[{case_id}]: Empty conversation")
			continue

		for j, turn in enumerate(conv):
			uc = turn.get("user_content", {})
			fr = turn.get("final_response", {})

			if not uc.get("parts"):
				issues.append(f"[{case_id}] turn[{j}]: Missing user_content.parts")

			if not fr.get("parts"):
				issues.append(f"[{case_id}] turn[{j}]: Missing final_response.parts")

			# Check for required fields in parts
			for k, part in enumerate(uc.get("parts", [])):
				if not part.get("text") and not part.get("inline_data"):
					issues.append(f"[{case_id}] turn[{j}] user_content.parts[{k}]: Missing 'text' or 'inline_data'")

	return issues


@pytest.fixture(params=["tts_prompt_crafter", "cartesia_tts_prompt_crafter"])
def agent_dir(request) -> Path:
	"""Parametrized fixture providing agent directory paths."""
	if request.param == "tts_prompt_crafter":
		return TTS_AGENT_DIR
	return CARTESIA_AGENT_DIR


# ── Tests ──────────────────────────────────────────────────────────────


class TestEvalSetDiscovery:
	"""Verify that eval set files exist for all agents."""

	def test_tts_prompt_crafter_has_evals(self) -> None:
		"""TTS Prompt Crafter should have at least one eval set."""
		evals = discover_eval_sets(TTS_AGENT_DIR)
		assert len(evals) >= 1, f"No .evalset.json files found in {TTS_AGENT_DIR}"

	def test_cartesia_agent_has_evals(self) -> None:
		"""Cartesia TTS agent should have at least one eval set."""
		evals = discover_eval_sets(CARTESIA_AGENT_DIR)
		assert len(evals) >= 1, f"No .evalset.json files found in {CARTESIA_AGENT_DIR}"


class TestEvalSetStructure:
	"""Validate the internal structure of every eval set."""

	@pytest.mark.parametrize(
		"eval_path",
		discover_eval_sets(TTS_AGENT_DIR) + discover_eval_sets(CARTESIA_AGENT_DIR),
		ids=lambda p: p.parent.name + "/" + p.stem,
	)
	def test_eval_set_structure(self, eval_path: Path) -> None:
		"""Each eval set must have valid structure."""
		assert eval_path.exists(), f"Eval set not found: {eval_path}"

		with Path(eval_path).open() as f:
			data = json.load(f)

		issues = _validate_eval_set_structure(data, eval_path.stem)
		assert not issues, f"Structural issues in {eval_path.relative_to(PROJECT_ROOT)}:\n" + "\n".join(
			f"  - {i}" for i in issues
		)

	def test_all_eval_sets_have_unique_ids(self) -> None:
		"""Eval set IDs across all agents must be unique."""
		seen_ids: dict[str, list[str]] = {}
		all_evals = discover_eval_sets(TTS_AGENT_DIR) + discover_eval_sets(CARTESIA_AGENT_DIR)

		for eval_path in all_evals:
			with Path(eval_path).open() as f:
				data = json.load(f)
			eval_id = data.get("eval_set_id", eval_path.stem)
			if eval_id not in seen_ids:
				seen_ids[eval_id] = []
			seen_ids[eval_id].append(str(eval_path))

		duplicates = {k: v for k, v in seen_ids.items() if len(v) > 1}
		assert not duplicates, f"Duplicate eval_set_id found: {duplicates}"


class TestEvalRunViaADK:
	"""Run eval sets through the ADK evaluation engine."""

	@pytest.mark.slow
	@pytest.mark.parametrize(
		"eval_path",
		discover_eval_sets(TTS_AGENT_DIR),
		ids=lambda p: p.stem,
	)
	def test_run_tts_eval_set(self, eval_path: Path) -> None:
		"""Run a TTS Prompt Crafter eval set through the ADK evaluator.

		This test requires the ADK evaluation module and a valid
		Gemini API key. It runs the agent against recorded conversation
		traces and scores responses.
		"""
		import sys

		sys.path.insert(0, str(Path(__file__).parent.parent))
		from evals.run_adk_eval import run_eval_via_adk

		result = run_eval_via_adk(eval_path, verbose=False)
		assert result.get("status") in ("completed", "validated_only"), f"Eval run failed: {result.get('error')}"

	@pytest.mark.slow
	@pytest.mark.skip(reason="Cartesia TTS agent tools not yet implemented")
	def test_run_cartesia_eval_set(self) -> None:
		"""Cartesia eval sets can be run once tools are implemented."""
