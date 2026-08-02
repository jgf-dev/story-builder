#!/usr/bin/env python3
"""ADK Eval Runner — Run Google ADK eval sets programmatically.

This script loads one or more .evalset.json files and executes them
against the configured ADK agents. Results are saved to the .adk/eval_history/
directory and printed to stdout.

Usage:
    # Run a specific eval set
    python evals/run_adk_eval.py --eval-set eval_set_2

    # Run all eval sets
    python evals/run_adk_eval.py --all

    # Run with verbose output
    python evals/run_adk_eval.py --eval-set eval_set_1 --verbose
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Ensure the project root is on sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Agent paths
TTS_AGENT_DIR = PROJECT_ROOT / ".agent" / "skills" / "tts-prompt-crafter"
CARTESIA_AGENT_DIR = PROJECT_ROOT / "src" / "storybuilder" / "cartesia"


def discover_eval_sets(agent_dir: Path) -> list[Path]:
    """Discover all .evalset.json files in an agent directory."""
    return sorted(agent_dir.glob("*.evalset.json"))


def load_eval_set(eval_set_path: Path) -> dict:
    """Load an ADK eval set JSON file."""
    with Path(eval_set_path).open(encoding="utf-8") as f:
        return json.load(f)


def print_eval_set_summary(eval_set: dict) -> None:
    """Print a summary of an eval set."""
    name = eval_set.get("name", eval_set.get("eval_set_id", "unknown"))
    cases = eval_set.get("eval_cases", [])
    print(f"\n{'=' * 60}")

    print(f"Eval Set: {name}")
    print(f"  Cases: {len(cases)}")
    for i, case in enumerate(cases):
        conv = case.get("conversation", [])
        eval_id = case.get("eval_id", f"case_{i}")
        turns = len(conv)
        first_msg = conv[0].get("user_content", {}).get("parts", [{}])[0].get("text", "")[:80] if conv else ""
        print(
            f'  [{i + 1}] {eval_id}: {turns} turn(s) — "{first_msg}..."'
            if first_msg
            else f"  [{i + 1}] {eval_id}: {turns} turn(s)",
        )
    print(f"{'=' * 60}")


def run_eval_via_adk(eval_set_path: Path, verbose: bool = False) -> dict:
    """Run an ADK eval set using the ADK CLI or programmatic API.

    This function attempts to use the ADK's built-in evaluation via the
    `AgentEvaluator.evaluate_eval_set()` API. If the ADK evaluation module
    is unavailable, it falls back to structural validation.

    Results are automatically saved to .adk/eval_history/ by the ADK.
    """
    eval_path = Path(eval_set_path)
    agent_dir = eval_path.parent

    eval_data = load_eval_set(eval_set_path)
    eval_name = eval_data.get("name", eval_data.get("eval_set_id", eval_path.stem))

    if verbose:
        print(f"\nRunning eval set: {eval_name}")
        print_eval_set_summary(eval_data)

    # Try loading the eval set via ADK's built-in file loader
    try:
        from google.adk.evaluation import AgentEvaluator
        from google.adk.evaluation.local_eval_sets_manager import load_eval_set_from_file

        original_cwd = _Path.cwd()
        os.chdir(str(agent_dir))

        try:
            # Load using ADK's file loader (handles both new and old formats)
            eval_set_id = eval_data.get("eval_set_id") or eval_data.get("name") or eval_path.stem
            pydantic_eval_set = load_eval_set_from_file(str(eval_path), eval_set_id)

            # Determine agent module path relative to the agent's directory
            # The agent module must be importable from the agent directory
            agent_module = _resolve_agent_module(agent_dir)

            # Run the evaluation asynchronously
            results = asyncio.run(
                AgentEvaluator.evaluate_eval_set(
                    agent_module=agent_module,
                    eval_set=pydantic_eval_set,
                    num_runs=1,
                    print_detailed_results=verbose,
                ),

            )

            # Print results summary
            print(f"\nResults for '{eval_name}':")
            if hasattr(results, "eval_case_results"):
                for case_result in results.eval_case_results:
                    case_id = getattr(case_result, "eval_id", "?")
                    metrics = getattr(case_result, "overall_eval_metric_results", [])
                    print(f"  Case '{case_id}':")
                    for metric in metrics:
                        metric_name = getattr(metric, "metric_name", "?")
                        score = getattr(metric, "score", None)
                        status = getattr(metric, "eval_status", None)
                        status_label = "?"
                        if status is not None:
                            try:
                                status_label = {1: "PASS", 2: "FAIL", 3: "SKIP", 4: "ERROR"}[int(status)]
                            except (KeyError, ValueError, TypeError):
                                status_label = str(status)

                        if score is not None:
                            print(f"    {metric_name}: {score:.4f} [{status_label}]")
                        else:
                            print(f"    {metric_name}: [{status_label}]")

            return {"status": "completed", "eval_set": eval_name}

        finally:
            os.chdir(original_cwd)

    except ImportError as e:
        logger.warning("ADK evaluation module not available: %s", e)
        logger.info("Falling back to structural validation.")
        issues = validate_eval_set_structure(eval_data, str(eval_path))
        return {
            "status": "validated_only",
            "eval_set": eval_name,
            "issues": issues,
            "error": str(e),
        }
    except Exception as e:  # pylint: disable=broad-except
        logger.exception("Error running eval set '%s'", eval_name)
        return {"status": "error", "eval_set": eval_name, "error": str(e)}


def _resolve_agent_module(agent_dir: Path) -> str:
    """Resolve the Python module path for an agent directory.

    E.g., for agent_dir = .../src/storybuilder/agents/tts_prompt_crafter
    returns 'storybuilder.agents.tts_prompt_crafter.agent'
    """
    src_dir = Path(__file__).parent.parent / "src"
    try:
        relative = agent_dir.resolve().relative_to(src_dir.resolve())
    except ValueError:
        # Fall back to the basename
        return f"{agent_dir.name}.agent"
    module = str(relative).replace("/", ".").replace("\\", ".")
    return f"{module}.agent"


def validate_eval_set_structure(eval_set: dict, file_path: str | None = None) -> list[str]:
    """Validate the structure of an ADK eval set without running it."""
    issues = []
    eval_id = eval_set.get("eval_set_id") or eval_set.get("name", "unknown")
    location = f" ({file_path})" if file_path else ""

    if not eval_set.get("eval_cases"):
        issues.append(f"[{eval_id}]{location} No eval_cases found")

    for i, case in enumerate(eval_set.get("eval_cases", [])):
        case_id = case.get("eval_id", f"case_{i}")
        conv = case.get("conversation", [])
        if not conv:
            issues.append(f"[{case_id}]{location} Empty conversation")
        for j, turn in enumerate(conv):
            uc = turn.get("user_content", {})
            if not uc.get("parts"):
                issues.append(f"[{case_id}]{location} turn[{j}] missing user_content parts")
            fr = turn.get("final_response", {})
            if not fr.get("parts"):
                issues.append(f"[{case_id}]{location} turn[{j}] missing final_response parts")

    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ADK evaluation sets")
    parser.add_argument(
        "--eval-set",
        type=str,
        help="Specific eval set name to run (e.g., 'eval_set_1')",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all discovered eval sets",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate eval set structure, don't run",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--agent",
        type=str,
        choices=["tts_prompt_crafter", "cartesia_tts_prompt_crafter", "all"],
        default="tts_prompt_crafter",
        help="Which agent's eval sets to run",
    )
    args = parser.parse_args()

    # Discover eval sets
    agent_dirs = []
    if args.agent in {"tts_prompt_crafter", "all"}:
        agent_dirs.append(TTS_AGENT_DIR)
    if args.agent in {"cartesia_tts_prompt_crafter", "all"}:
        agent_dirs.append(CARTESIA_AGENT_DIR)

    all_eval_sets = []
    for agent_dir in agent_dirs:
        if agent_dir.exists():
            all_eval_sets.extend(discover_eval_sets(agent_dir))

    if not all_eval_sets:
        print("No eval sets found.")
        return

    # Filter by name if specified
    if args.eval_set:
        matched = [p for p in all_eval_sets if args.eval_set in p.stem]
        if not matched:
            print(f"No eval set matching '{args.eval_set}' found.")
            print(f"Available: {[p.stem for p in all_eval_sets]}")
            return
        all_eval_sets = matched

    if args.validate_only:
        print(f"Validating {len(all_eval_sets)} eval set(s)...")
        for eval_path in all_eval_sets:
            eval_set = load_eval_set(eval_path)
            issues = validate_eval_set_structure(eval_set, str(eval_path))
            print(f"\n{'=' * 60}")

            print(f"File: {eval_path.relative_to(PROJECT_ROOT)}")
            print(f"  Cases: {len(eval_set.get('eval_cases', []))}")
            if issues:
                print(f"  Issues ({len(issues)}):")
                for issue in issues:
                    print(f"    ⚠ {issue}")
            else:
                print("  ✅ No structural issues found")
        return

    if not args.eval_set and not args.all:
        # List available eval sets
        print(f"Available eval sets ({len(all_eval_sets)}):")
        for eval_path in all_eval_sets:
            print(f"  • {eval_path.relative_to(PROJECT_ROOT)}")
        print("\nRun with --eval-set <name> or --all to execute.")
        return

    # Run eval sets
    print(f"Running {len(all_eval_sets)} eval set(s)...")
    for eval_path in all_eval_sets:
        try:
            run_eval_via_adk(eval_path, verbose=args.verbose)
        except Exception as e:
            logger.exception("Failed to run %s: %s", eval_path.name, e)


if __name__ == "__main__":
    main()
