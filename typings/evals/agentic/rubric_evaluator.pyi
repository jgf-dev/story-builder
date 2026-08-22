from _typeshed import Incomplete

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

logger: Logger


@dataclass
class RubricDimension:
    name: str
    description: str
    weight: float
    scorer: Callable | None = None

    def __init__(self, name: str, description: str, weight: float, scorer: Incomplete = ...) -> None: ...


@dataclass
class RubricScore:
    dimension: str
    score: float
    weight: float
    weighted_score: float
    reason: str
    details: dict[str, Any] | None = None

    def __init__(self, dimension: str, score: float, weight: float, weighted_score: float, reason: str, details: dict[str, Any] | None = ...) -> None: ...


@dataclass
class RubricEvaluationResult:
    overall_score: float
    dimension_scores: list[RubricScore]
    passed: bool
    threshold: float
    summary: str

    def __init__(self, overall_score: float, dimension_scores: list[RubricScore], passed: bool, threshold: float, summary: str) -> None: ...


class RubricEvaluator:
    dimensions: list[RubricDimension]
    threshold: float

    def __init__(self, dimensions: list[RubricDimension], threshold: float = 0.7) -> None: ...

    def evaluate(self, agent_response: str, task: str, conversation_history: list[dict[str, Any]] | None = None, tool_calls: list[dict[str, Any]] | None = None) -> RubricEvaluationResult: ...


def default_llm_judge_scorer(llm_client: Any, model_name: str) -> Callable: ...
