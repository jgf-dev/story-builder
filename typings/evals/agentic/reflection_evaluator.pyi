from _typeshed import Incomplete

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

logger: Logger


@dataclass
class CritiqueResult:
    dimension: str
    status: str
    score: float
    feedback: str
    details: dict[str, Any] | None = None

    def __init__(self, dimension: str, status: str, score: float, feedback: str, details: dict[str, Any] | None = ...) -> None: ...


@dataclass
class ReflectionRound:
    iteration: int
    critiques: list[CritiqueResult]
    all_pass: bool
    overall_score: float

    def __init__(self, iteration: int, critiques: list[CritiqueResult], all_pass: bool, overall_score: float) -> None: ...


@dataclass
class ReflectionResult:
    output: str
    rounds: list[ReflectionRound]
    converged: bool = False
    total_iterations: int = 0

    def __init__(self, output: str, rounds: list[ReflectionRound] = ..., converged: bool = ..., total_iterations: int = ...) -> None: ...


class ReflectionEvaluator:
    criteria: list[dict[str, str]]
    max_iterations: int
    score_threshold: float

    def __init__(self, criteria: list[dict[str, str]], score_threshold: float = 0.8, max_iterations: int = 3) -> None: ...

    def evaluate(self, agent_response: str, task: str, conversation_history: list[dict[str, Any]] | None = None) -> ReflectionResult: ...


class LLMJudgeReflectionEvaluator(ReflectionEvaluator):
    judge_fn: Incomplete

    def __init__(self, judge_fn: Callable, criteria: list[dict[str, str]], score_threshold: float = 0.8, max_iterations: int = 3) -> None: ...
