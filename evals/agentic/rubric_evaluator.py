"""Rubric-based evaluation for ADK agent outputs.

Scores agent outputs against weighted evaluation dimensions using
configurable rubrics. Supports LLM-as-judge and deterministic scorers.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass

from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class RubricDimension:
    """A single dimension in the evaluation rubric."""

    name: str
    description: str
    weight: float  # 0.0 - 1.0, must sum to 1.0 across all dimensions
    scorer: Callable | None = None  # Optional custom scorer function


@dataclass
class RubricScore:
    """Score for a single rubric dimension."""

    dimension: str
    score: float  # 1-5 scale
    weight: float
    weighted_score: float
    reason: str
    details: dict[str, Any] | None = None


@dataclass
class RubricEvaluationResult:
    """Complete rubric evaluation result."""

    overall_score: float  # 0.0 - 1.0
    dimension_scores: list[RubricScore]
    passed: bool
    threshold: float
    summary: str


class RubricEvaluator:
    """Weighted rubric-based evaluation for agent outputs.

    Scores outputs against multiple dimensions (e.g., accuracy, clarity,
    completeness) using configurable weights and scorer functions.

    Example:
        evaluator = RubricEvaluator(
            dimensions=[
                RubricDimension(name="task_adherence", description="Follows the assigned task",
                                weight=0.4),
                RubricDimension(name="tool_usage", description="Correct tool usage",
                                weight=0.3),
                RubricDimension(name="response_clarity", description="Clear and well-structured",
                                weight=0.3),
            ],
            threshold=0.7,
        )
        result = evaluator.evaluate(agent_response="...", task="...")
    """

    def __init__(
        self,
        dimensions: list[RubricDimension],
        threshold: float = 0.7,
    ):
        total_weight = sum(d.weight for d in dimensions)
        if abs(total_weight - 1.0) > 0.001:
            logger.warning(
                "Rubric weights sum to %.2f (expected 1.0). Normalizing.",
                total_weight,
            )
            for d in dimensions:
                d.weight /= total_weight

        self.dimensions = dimensions
        self.threshold = threshold

    def evaluate(
        self,
        agent_response: str,
        task: str,
        conversation_history: list[dict[str, Any]] | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> RubricEvaluationResult:
        """Evaluate an agent response against the rubric.

        Args:
            agent_response: The agent's final response text.
            task: The original task/query.
            conversation_history: Optional full conversation.
            tool_calls: Optional list of tool calls made.

        Returns:
            RubricEvaluationResult with dimension scores and overall score.
        """
        context = {
            "task": task,
            "conversation_history": conversation_history or [],
            "tool_calls": tool_calls or [],
            "response": agent_response,
        }

        dimension_scores = []
        for dim in self.dimensions:
            score = self._score_dimension(dim, context)
            weighted = (score - 1.0) / 4.0 * dim.weight  # Normalize 1-5 to 0-1, apply weight
            dimension_scores.append(
                RubricScore(
                    dimension=dim.name,
                    score=score,
                    weight=dim.weight,
                    weighted_score=score / 5.0 * dim.weight,
                    reason=f"Override scorer for '{dim.name}' to get detailed feedback",
                    details={"criterion_description": dim.description},
                ),

            )

        overall_score = sum(s.weighted_score for s in dimension_scores)
        passed = overall_score >= self.threshold

        total = overall_score
        max_possible = sum(d.weight for d in self.dimensions)
        summary = (
            f"Overall score: {overall_score:.2f}/{max_possible:.2f} "
            f"({'PASS' if passed else 'FAIL'} at threshold {self.threshold})"
        )

        return RubricEvaluationResult(
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            passed=passed,
            threshold=self.threshold,
            summary=summary,
        )

    def _score_dimension(self, dim: RubricDimension, context: dict) -> float:
        """Score a single dimension. Uses custom scorer if provided."""
        if dim.scorer:
            try:
                return dim.scorer(context)
            except Exception as e:
                logger.error("Scorer for '%s' failed: %s", dim.name, e)
                return 1.0  # Default to minimum on error
        return 3.0  # Default mid-range score


def default_llm_judge_scorer(
    llm_client: Any,
    model_name: str,
) -> Callable:
    """Create an LLM judge scorer function.

    Args:
        llm_client: An LLM client with a generate() method.
        model_name: The model name to use for judging.

    Returns:
        A scorer function compatible with RubricDimension.
    """

    def scorer(context: dict) -> float:
        prompt = f"""You are an expert evaluator. Score the following agent response
on a scale of 1 (worst) to 5 (best).

Task: {context.get("task", "N/A")}

Agent Response: {context.get("response", "N/A")}


Return only a number from 1 to 5."""
        try:
            result = llm_client.generate(prompt, model=model_name)
            score = float(result.strip())
            return max(1.0, min(5.0, score))
        except Exception as e:
            logger.error("LLM judge failed: %s", e)
            return 3.0

    return scorer
