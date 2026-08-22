# Evaluation Framework — StoryBuilder ADK Agents

This directory contains the evaluation framework for the Google ADK agents in the StoryBuilder project. It provides three complementary evaluation approaches:

| Approach | Description | Location |
|----------|-------------|----------|
| **ADK Built-in Eval** | Conversation replay with automated metrics (tool use, response match, task success) | `.evalset.json` files in agent directories |
| **Agentic Evaluation** | Reflection loops, rubric-based scoring, and LLM-as-judge patterns | `evals/agentic/` |
| **Pytest Integration** | Discoverable test cases in VS Code Test Explorer and CI | `evals/test_*.py` |

## Prerequisites

- Python 3.12+ with `uv`
- `uv sync --all-extras --dev` completes
- spaCy models: `python -m spacy download en_core_web_sm`
- `.env` with `GEMINI_API_KEY` (or Vertex AI credentials for the ADK agents)

## Setup

### 1. Install Dependencies

```bash
uv sync --all-extras --dev
```

### 2. VS Code Test Explorer

The `.vscode/settings.json` is already configured. Open the **Testing** panel (flask icon in the activity bar) to see all discovered tests.

### 3. Environment Variables

Ensure `.env` contains:

```env
GEMINI_API_KEY=your_key_here        # For ADK agent model access
# Or for Vertex AI:
# GOOGLE_CLOUD_PROJECT=your_project
# GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
```

## Running Evaluations

### Via VS Code Test Explorer (Recommended)

1. Open the **Testing** panel (🧪 flask icon in the activity bar)
2. Click **▶️ Run All Tests** or select individual tests
3. Results appear inline with pass/fail status and detailed output

### Via Terminal

```bash
# Run all evaluation tests (fast tests only)
uv run pytest evals/ -v -m "not slow"

# Run specific test class
uv run pytest evals/test_adk_eval_sets.py -v -k "TestEvalSetStructure"

# Run agentic evaluation tests
uv run pytest evals/test_tts_prompt_crafter_agentic.py -v

# Run slow tests (full pipeline + ADK eval engine)
uv run pytest evals/ -v -m "slow"

# Run all tests
uv run pytest evals/ -v
```

### Via ADK CLI

```bash
# From the agent directory, run the ADK eval command
cd src/storybuilder/agents/tts_prompt_crafter
adk eval eval_set_1
```

### Via the ADK Eval Runner Script

```bash
# List available eval sets
uv run python evals/run_adk_eval.py

# Validate eval set structure
uv run python evals/run_adk_eval.py --validate-only

# Run a specific eval set
uv run python evals/run_adk_eval.py --eval-set eval_set_1

# Run all eval sets for the TTS agent
uv run python evals/run_adk_eval.py --all

# Run all eval sets with verbose output
uv run python evals/run_adk_eval.py --all --verbose
```

## Test Structure

### `test_adk_eval_sets.py` — ADK Eval Set Validation

| Test | Description | Markers |
|------|-------------|---------|
| `TestEvalSetDiscovery` | Verifies `.evalset.json` files exist for each agent | — |
| `TestEvalSetStructure` | Validates internal schema of every eval set | — |
| `TestEvalRunViaADK` | Runs eval sets through the ADK evaluation engine | `slow` |

### `test_tts_prompt_crafter_agentic.py` — Agentic Evaluation

| Test | Description | Markers |
|------|-------------|---------|
| `TestTTSPromptCrafterGreetings` | Rubric-based evaluation of greeting responses | `agentic` |
| `TestTTSPromptCrafterPipeline` | Full pipeline execution (story → scenes) | `slow`, `agentic` |
| `TestTTSPromptCrafterEdgeCases` | Error handling for missing paths, empty queries | `agentic` |
| `TestTTSPromptCrafterReflection` | Self-reflection evaluation of output quality | `agentic` |

## Evaluation Approaches

### 1. ADK Built-in Eval Sets (`.evalset.json`)

Recorded conversation traces that the ADK replays and scores against built-in metrics:

- **`multi_turn_task_success_v1`**: Did the agent complete the task?
- **`multi_turn_tool_use_quality_v1`**: Were tools used correctly?
- **`final_response_match_v2`**: Did the final response match expectations?
- **`rubric_based_*`**: Custom rubric scoring for response quality and tool use

Found in each agent's directory, e.g.:
```
src/storybuilder/agents/tts_prompt_crafter/eval_set_1.evalset.json
src/storybuilder/agents/tts_prompt_crafter/.adk/eval_history/*.evalset_result.json
```

### 2. Agentic Evaluation Patterns

The `evals/agentic/` package provides reusable evaluation utilities:

- **`ReflectionEvaluator`**: Self-critique loop — evaluates output, identifies failures, refines (3-iteration max)
- **`LLMJudgeReflectionEvaluator`**: Same loop but with an external LLM judge function
- **`RubricEvaluator`**: Weighted multi-dimension scoring with configurable thresholds
- **`RubricDimension`**: Single evaluation dimension with weight, description, and custom scorer

### 3. pytest Integration

Every test is discoverable in VS Code Test Explorer and runnable via `pytest`. Tests use:

- **`conftest.py`** fixtures: `adk_events` (run query through ADK runner), `tts_agent`, `tts_runner`, `load_jsonl`
- **`@pytest.mark.slow`**: Skips full pipeline tests during quick iteration
- **Parametrized tests**: Each query/scenario is a separate test case

## Adding New Evaluation Datasets

### ADK Eval Sets

Create a new `.evalset.json` file in the agent's directory:

```json
{
  "eval_set_id": "my_new_eval",
  "name": "my_new_eval",
  "eval_cases": [
    {
      "eval_id": "case_1",
      "conversation": [
        {
          "invocation_id": "...",
          "user_content": {
            "parts": [{"text": "Your test query here"}],
            "role": "user"
          },
          "final_response": {
            "parts": [{"text": "Expected response (optional)"}],
            "role": "model"
          }
        }
      ]
    }
  ]
}
```

The easiest way to create eval sets is to run the agent in the ADK dev UI and export conversations.

### Agentic Evaluation Tests

Add new parametrized test methods to the existing test classes or create new test files:

```python
@pytest.mark.parametrize("query", ["new query 1", "new query 2"])
def test_new_scenario(self, adk_events, query):
	events = adk_events(query)
	# ... assertions ...
```

## Viewing Results

### VS Code Test Explorer
Tests appear in the sidebar with pass/fail status. Click any test to see detailed output.

### ADK Eval Results
After running ADK eval sets, results are saved to:
```
src/storybuilder/agents/tts_prompt_crafter/.adk/eval_history/*.evalset_result.json
```

### Test Output
Run with `-v` or `--verbose` for detailed output including rubric scores per dimension:
```bash
uv run pytest evals/test_tts_prompt_crafter_agentic.py -v --tb=long
```
