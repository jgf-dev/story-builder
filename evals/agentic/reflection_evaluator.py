"""Self-reflection evaluation pattern for ADK agents.

Evaluates agent outputs through iterative self-critique and refinement
loops. Each cycle generates a critique, scores it against criteria,
and refines until all criteria pass or the iteration limit is reached.

Based on the agentic-eval skill patterns.
"""


import logging
from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class CritiqueResult:
    """Result of a single critique evaluation."""

    dimension: str
    status: str  # "PASS" or "FAIL"
    score: float  # 0.0 - 1.0
    feedback: str
    details: dict[str, Any] | None = None


@dataclass
class ReflectionRound:
    """Single round of reflection."""

    iteration: int
    critiques: list[CritiqueResult]
    all_pass: bool
    overall_score: float


@dataclass
class ReflectionResult:
    """Final result of the reflection loop."""

    output: str
    rounds: list[ReflectionRound] = field(default_factory=list)
    converged: bool = False
    total_iterations: int = 0


class ReflectionEvaluator:
    """Self-reflection evaluator for agent outputs.

    Usage:
        evaluator = ReflectionEvaluator(criteria=[
            {"name": "task_completeness", "description": "All steps of the task are addressed"},
            {"name": "tool_usage", "description": "Tools are used correctly and efficiently"},
        ])
        result = evaluator.evaluate(agent_response="...", task="...")
    """

    def __init__(
        self,
        criteria: list[dict[str, str]],
        score_threshold: float = 0.8,
        max_iterations: int = 3,
    ):
        self.criteria = criteria
        self.score_threshold = score_threshold
        self.max_iterations = max_iterations

    def evaluate(
        self,
        agent_response: str,
        task: str,
        conversation_history: list[dict[str, Any]] | None = None,
    ) -> ReflectionResult:
        """Run the reflection loop on an agent's response.

        Args:
            agent_response: The agent's final response text.
            task: The original task/query given to the agent.
            conversation_history: Optional full conversation history.

        Returns:
            ReflectionResult with all rounds and final verdict.
        """
        output = agent_response
        result = ReflectionResult(output=output)
        context = {
            "task": task,
            "conversation_history": conversation_history or [],
        }

        for iteration in range(self.max_iterations):
            critiques = self._critique(output, context)
            all_pass = all(c.status == "PASS" for c in critiques)
            overall_score = sum(c.score for c in critiques) / len(critiques) if critiques else 0.0

            round_result = ReflectionRound(
                iteration=iteration + 1,
                critiques=critiques,
                all_pass=all_pass,
                overall_score=overall_score,
            )
            result.rounds.append(round_result)

            if all_pass or overall_score >= self.score_threshold:
                result.converged = True
                result.total_iterations = iteration + 1
                logger.info(
                    "Reflection converged at iteration %d (score=%.2f, threshold=%.2f)",
                    iteration + 1,
                    overall_score,
                    self.score_threshold,
                )
                return result

            if iteration < self.max_iterations - 1:
                output = self._refine(output, critiques, context)
                result.output = output

        result.total_iterations = self.max_iterations
        logger.info(
            "Reflection reached max iterations (%d) without convergence (score=%.2f)",
            self.max_iterations,
            result.rounds[-1].overall_score if result.rounds else 0.0,
        )
        return result

    def _critique(self, output: str, context: dict) -> list[CritiqueResult]:
        """Evaluate the output against all criteria.

        This is a structured evaluation - in production this would call
        an LLM judge. Here we provide a deterministic scoring framework
        that test code can extend with custom judges.
        """
        return [
            CritiqueResult(
                dimension=c["name"],
                status="UNKNOWN",
                score=0.0,
                feedback=f"Override this method to implement {c['name']} evaluation. "
                f"Criterion: {c.get('description', 'No description')}",
                details={"criterion": c},
            )
            for c in self.criteria
        ]

    def _refine(self, output: str, critiques: list[CritiqueResult], context: dict) -> str:
        """Refine the output based on critique feedback.

        Override this in subclasses to implement LLM-based refinement.
        """
        failed = [c for c in critiques if c.status == "FAIL"]
        feedback = {c.dimension: c.feedback for c in failed}
        logger.info("Refinement needed for dimensions: %s", list(feedback.keys()))
        return output


class LLMJudgeReflectionEvaluator(ReflectionEvaluator):
    """Reflection evaluator that uses an LLM judge for evaluation.

    To use, create an LLM judge function and pass it in.

    Example:
        def judge(output, task, criterion):
            # Call an LLM to evaluate
            return CritiqueResult(dimension="quality", status="PASS", score=0.9, feedback="...")

        evaluator = LLMJudgeReflectionEvaluator(
            judge_fn=judge,
            criteria=[{"name": "quality", "description": "Overall quality"}]
        )
    """

    def __init__(
        self,
        judge_fn: Callable,
        criteria: list[dict[str, str]],
        score_threshold: float = 0.8,
        max_iterations: int = 3,
    ):
        super().__init__(criteria, score_threshold, max_iterations)
        self.judge_fn = judge_fn

    def _critique(self, output: str, context: dict) -> list[CritiqueResult]:
        results = []
        for criterion in self.criteria:
            try:
                result = self.judge_fn(
                    output=output,
                    task=context.get("task", ""),
                    criterion=criterion,
                )
                results.append(result)
            except Exception as e:
                logger.error("Judge function failed for criterion '%s': %s", criterion["name"], e)
                results.append(
                    CritiqueResult(
                        dimension=criterion["name"],
                        status="FAIL",
                        score=0.0,
                        feedback=f"Judge error: {e}",
                    ),

                )
        return results
