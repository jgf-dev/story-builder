import logging
from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field
from typing import Any

logger: Logger


@dataclass
class CritiqueResult:
    dimension: str
    status: str
    score: float
    feedback: str
    details: dict[str, Any] | None = None


@dataclass
class ReflectionRound:
    iteration: int
    critiques: list[CritiqueResult]
    all_pass: bool
    overall_score: float


@dataclass
class ReflectionResult:
    output: str
    rounds: list[ReflectionRound]
    converged: bool = False
    total_iterations: int = 0


class ReflectionEvaluator:
    def __init__(self, criteria: list[dict[str, str]], score_threshold: float = 0.8, max_iterations: int = 3) -> None: ...

    def evaluate(self, agent_response: str, task: str, conversation_history: list[dict[str, Any]] | None = None) -> ReflectionResult: ...


class LLMJudgeReflectionEvaluator(ReflectionEvaluator):
    def __init__(self, judge_fn: Callable, criteria: list[dict[str, str]], score_threshold: float = 0.8, max_iterations: int = 3) -> None: ...
