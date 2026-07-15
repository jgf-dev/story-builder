from _typeshed import Incomplete

import pytest
from evals.agentic.reflection_evaluator import ReflectionEvaluator
from evals.agentic.rubric_evaluator import RubricDimension
from evals.agentic.rubric_evaluator import RubricEvaluator

TTS_EVALUATION_RUBRIC: Incomplete
GREETING_QUERIES: list[str]
PIPELINE_QUERIES: list[str]
EDGE_CASES: list[str]


class TestTTSPromptCrafterGreetings:
    @pytest.mark.parametrize("query", GREETING_QUERIES)
    def test_greeting_response(self, adk_events: Incomplete, query: Incomplete) -> None: ...


class TestTTSPromptCrafterPipeline:
    @pytest.mark.slow
    @pytest.mark.parametrize("query", PIPELINE_QUERIES)
    def test_pipeline_execution(self, adk_events: Incomplete, query: Incomplete) -> None: ...


class TestTTSPromptCrafterEdgeCases:
    def test_missing_story(self, adk_events: Incomplete) -> None: ...

    def test_empty_query(self, adk_events: Incomplete) -> None: ...


class TestTTSPromptCrafterReflection:
    REFLECTION_CRITERIA: list[dict[str, str]]

    @pytest.mark.parametrize("query", GREETING_QUERIES[:2])
    def test_self_reflection_on_greetings(self, adk_events: Incomplete, query: Incomplete) -> None: ...
