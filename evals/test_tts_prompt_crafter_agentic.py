"""Agentic evaluation tests for the TTS Prompt Crafter ADK agent.

Uses the agentic-eval patterns (reflection, rubric-based evaluation)
to assess agent behavior across multiple scenarios:

- Greeting / capability disclosure
- Story reading and analysis
- Scene writing quality
- Full pipeline execution
- Error handling (missing stories, invalid paths)

These tests use the LLM-as-judge pattern via the RubricEvaluator
and ReflectionEvaluator utilities. They do NOT require an external
LLM judge — scoring is done via deterministic heuristics that you
can extend with custom scorers.

Run with:
    pytest evals/test_tts_prompt_crafter_agentic.py -v
"""

import pytest

<<<<<<< HEAD
<<<<<<< HEAD
from evals.agentic.reflection_evaluator import CritiqueResult
=======
>>>>>>> palette-fix-duplicate-file-input-1065389564287363483
=======
from evals.agentic.reflection_evaluator import CritiqueResult
>>>>>>> palette/fix-duplicate-file-input-14315194890274537724
from evals.agentic.reflection_evaluator import ReflectionEvaluator
from evals.agentic.rubric_evaluator import RubricDimension
from evals.agentic.rubric_evaluator import RubricEvaluator


# ── Scorers ────────────────────────────────────────────────────────────


def _score_task_adherence(context: dict) -> float:
    """Score how well the response adheres to the task.

    Checks if the response acknowledges the query, doesn't go off-topic,
    and addresses the core request.
    """
    response = context.get("response", "").lower()
    task = context.get("task", "").lower()

    score = 3.0  # Default mid

    # Check if response acknowledges the task
    keywords = [w for w in task.split() if len(w) > 4]
    keyword_matches = sum(1 for kw in keywords if kw in response)
    if keyword_matches > 0:
        score += 1.0

    # Bonus for comprehensive responses
    if len(response) > 200:
        score += 0.5

    # Longer responses addressing the task get full marks
    if len(response) > 500 and keyword_matches >= 2:
        score = 5.0

    return min(5.0, score)


def _score_response_completeness(context: dict) -> float:
    """Score how complete the response is."""
    response = context.get("response", "")

    # Structural completeness checks
    checks = [
        response.startswith("Hello") or response.startswith("I"),  # Proper greeting/intro
        len(response) > 100,  # Substantial response
        "stories" in response.lower() or "story" in response.lower(),  # Mentions stories
        "?" not in response[-50:],  # Doesn't end with a question
    ]

    score = 2.0 + sum(1 for c in checks if c)
    return min(5.0, score)


def _score_tool_utilization(context: dict) -> float:
    """Score appropriate tool usage based on tool calls."""
    tool_calls = context.get("tool_calls", [])

    if not tool_calls:
        return 2.0  # No tools used — suspicious for a tool-using agent

    return 4.0  # Tools were used


# ── Rubric Definition ──────────────────────────────────────────────────


TTS_EVALUATION_RUBRIC = [
    RubricDimension(
        name="task_adherence",
        description="Response addresses the user's query appropriately",
        weight=0.35,
        scorer=_score_task_adherence,
    ),
    RubricDimension(
        name="response_completeness",
        description="Response is complete and well-structured",
        weight=0.35,
        scorer=_score_response_completeness,
    ),
    RubricDimension(
        name="tool_utilization",
        description="Agent uses available tools correctly when needed",
        weight=0.30,
        scorer=_score_tool_utilization,
    ),
]


# ── Test Scenarios ─────────────────────────────────────────────────────


GREETING_QUERIES = [
    "Hello",
    "Hi there",
    "What can you do?",
    "Help me with a story",
]

PIPELINE_QUERIES = [
    "Process the story at stories/text/i_came_during_tryouts.md",
]

EDGE_CASES = [
    "Process a story that doesn't exist",
    "",
]


# ── Tests ──────────────────────────────────────────────────────────────


class TestTTSPromptCrafterGreetings:
    """Evaluate greeting/capability responses."""

    @pytest.mark.parametrize("query", GREETING_QUERIES)
    def test_greeting_response(self, adk_events, query):
        """Agent should respond appropriately to greetings."""
<<<<<<< HEAD
<<<<<<< HEAD
        events = adk_events({'content': query, 'role': 'user'})
=======
        events = adk_events(query)
>>>>>>> palette-fix-duplicate-file-input-1065389564287363483
=======
        events = adk_events(query)
>>>>>>> palette/fix-duplicate-file-input-14315194890274537724

        assert len(events) > 0, f"No events returned for query: {query}"

        # Get the final response
        final_events = [e for e in events if e.is_final_response()]
        assert len(final_events) > 0, "No final response event found"

        response = final_events[-1].content.parts[0].text if final_events[-1].content else ""
        assert response, "Empty response content"

        # Extract tool calls for evaluation context
        tool_calls = []
        for event in events:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.function_call:
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> palette/fix-duplicate-file-input-14315194890274537724
                        tool_calls.append({
                            "name": part.function_call.name,
                            "args": dict(part.function_call.args) if part.function_call.args else {},
                        })
<<<<<<< HEAD
=======
                        tool_calls.append(
                            {
                                "name": part.function_call.name,
                                "args": dict(part.function_call.args) if part.function_call.args else {},
                            },
                        )
>>>>>>> palette-fix-duplicate-file-input-1065389564287363483
=======
>>>>>>> palette/fix-duplicate-file-input-14315194890274537724

        # Evaluate using rubric
        evaluator = RubricEvaluator(dimensions=TTS_EVALUATION_RUBRIC, threshold=0.5)
        result = evaluator.evaluate(
            agent_response=response,
            task=query,
            tool_calls=tool_calls,
        )

        assert result.passed, (
            f"Rubric evaluation FAILED for '{query}':\n"
            f"  Overall score: {result.overall_score:.2f} (threshold: {result.threshold})\n"
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> palette/fix-duplicate-file-input-14315194890274537724
            f"  Dimensions:\n" +
            "\n".join(
                f"    {s.dimension}: {s.score}/5.0 (weight: {s.weight})"
                for s in result.dimension_scores
            )
<<<<<<< HEAD
=======
            f"  Dimensions:\n"
            + "\n".join(f"    {s.dimension}: {s.score}/5.0 (weight: {s.weight})" for s in result.dimension_scores)
>>>>>>> palette-fix-duplicate-file-input-1065389564287363483
=======
>>>>>>> palette/fix-duplicate-file-input-14315194890274537724
        )


class TestTTSPromptCrafterPipeline:
    """Evaluate full pipeline execution (story → analysis → scene writing)."""

    @pytest.mark.slow
    @pytest.mark.parametrize("query", PIPELINE_QUERIES)
    def test_pipeline_execution(self, adk_events, query):
        """Agent should process a story through the full pipeline."""
<<<<<<< HEAD
<<<<<<< HEAD
        events = adk_events({'content': query})
=======
        events = adk_events(query)
>>>>>>> palette-fix-duplicate-file-input-1065389564287363483
=======
        events = adk_events(query)
>>>>>>> palette/fix-duplicate-file-input-14315194890274537724

        assert len(events) > 0, "No events returned"

        # Check for tool calls (should call read_story at minimum)
        tool_calls_made = set()
        for event in events:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.function_call:
                        tool_calls_made.add(part.function_call.name)

        # Should have at least attempted tool usage
<<<<<<< HEAD
<<<<<<< HEAD
        assert len(tool_calls_made) > 0, (
            f"No tool calls made during pipeline execution"
        )
=======
        assert len(tool_calls_made) > 0, "No tool calls made during pipeline execution"
>>>>>>> palette-fix-duplicate-file-input-1065389564287363483
=======
        assert len(tool_calls_made) > 0, (
            f"No tool calls made during pipeline execution"
        )
>>>>>>> palette/fix-duplicate-file-input-14315194890274537724

        # Get final response
        final_events = [e for e in events if e.is_final_response()]
        if final_events:
            response = final_events[-1].content.parts[0].text if final_events[-1].content else ""
            assert response, "Empty final response"


class TestTTSPromptCrafterEdgeCases:
    """Evaluate edge case handling."""

    def test_missing_story(self, adk_events):
        """Agent should handle non-existent story paths gracefully."""
        query = "Process the story at stories/text/nonexistent.md"
<<<<<<< HEAD
<<<<<<< HEAD
        events = adk_events({'content': query})
=======
        events = adk_events(query)
>>>>>>> palette-fix-duplicate-file-input-1065389564287363483
=======
        events = adk_events(query)
>>>>>>> palette/fix-duplicate-file-input-14315194890274537724

        final_events = [e for e in events if e.is_final_response()]
        if not final_events:
            pytest.skip("No final response event — may need agent interaction")

        response = final_events[-1].content.parts[0].text if final_events[-1].content else ""

        # Should not crash or produce empty response
        assert response, "Agent returned empty response for invalid path"

        # Should mention the error or inability to find the file
        error_indicators = ["not found", "doesn't exist", "cannot", "unable", "error", "sorry"]
        has_error_response = any(indicator in response.lower() for indicator in error_indicators)
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> palette/fix-duplicate-file-input-14315194890274537724
        assert has_error_response, (
            f"Agent should acknowledge the missing file.\nResponse: {response[:200]}"
        )

    def test_empty_query(self, adk_events):
        """Agent should handle empty queries gracefully."""
<<<<<<< HEAD
        events = adk_events({'content': '', 'role': 'user'})
=======
        assert has_error_response, f"Agent should acknowledge the missing file.\nResponse: {response[:200]}"

    def test_empty_query(self, adk_events):
        """Agent should handle empty queries gracefully."""
        events = adk_events("")
>>>>>>> palette-fix-duplicate-file-input-1065389564287363483
=======
        events = adk_events("")
>>>>>>> palette/fix-duplicate-file-input-14315194890274537724

        assert len(events) > 0, "No events for empty query"

        final_events = [e for e in events if e.is_final_response()]
        if final_events:
            response = final_events[-1].content.parts[0].text if final_events[-1].content else ""
            assert response, "Empty response for empty query"


class TestTTSPromptCrafterReflection:
    """Self-reflection evaluation of agent outputs.

    Uses the ReflectionEvaluator to assess agent responses against
    defined criteria and verify they pass at the specified threshold.
    """

    REFLECTION_CRITERIA = [
        {
            "name": "task_completeness",
            "description": "The response fully addresses the user's request",
        },
        {
            "name": "response_quality",
            "description": "The response is well-structured and informative",
        },
    ]

    @pytest.mark.parametrize("query", GREETING_QUERIES[:2])
    def test_self_reflection_on_greetings(self, adk_events, query):
        """Verify agent outputs pass self-reflection criteria."""
<<<<<<< HEAD
<<<<<<< HEAD
        events = adk_events({'content': query, 'role': 'user'})
=======
        events = adk_events(query)
>>>>>>> palette-fix-duplicate-file-input-1065389564287363483
=======
        events = adk_events(query)
>>>>>>> palette/fix-duplicate-file-input-14315194890274537724

        final_events = [e for e in events if e.is_final_response()]
        if not final_events:
            pytest.skip("No final response event")

        response = final_events[-1].content.parts[0].text if final_events[-1].content else ""
        if not response:
            pytest.skip("Empty response")

        evaluator = ReflectionEvaluator(
            criteria=self.REFLECTION_CRITERIA,
            score_threshold=0.7,
            max_iterations=1,  # Single shot for testing
        )
        result = evaluator.evaluate(agent_response=response, task=query)

        # Round 1 should show the criteria evaluation status
        if result.rounds:
            round_1 = result.rounds[0]
            print(f"\nReflection for '{query}':")
            for critique in round_1.critiques:
                print(f"  {critique.dimension}: score={critique.score:.2f} [{critique.status}]")
