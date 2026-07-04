# StoryBuilder Open Tasks Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Address all open items in TASKS.md across 5 phases: database improvements, NER refinement, TTS engine enhancements, UI scaffolding, and codebase cleanup.

**Architecture:** Each phase is independent and can be shipped separately. Changes follow the existing patterns: argparse CLIs, unittest-based tests, src-layout package structure, and the established db.py module API.

**Tech Stack:** Python 3.12, SQLite/FTS5, spaCy, Google GenAI SDK, Cartesia SDK, Google ADK, Streamlit (for UI).

---

## Phase 1: Database Improvements

### Task 1: Batch FTS Optimize for All Partitions

**Objective:** Implement `optimize_fts_all()` that scans the partition directory and runs the FTS optimize PRAGMA on every `.db` file, not just currently-loaded connections.

**Files:**
- Modify: `src/storybuilder/downloader/db.py:305-317`
- Test: `tests/test_database.py`

**Approach:** Add a new function `optimize_fts_all(db_dir: str)` that:
1. Globs `*.db` in `db_dir`
2. Opens each with a temporary connection
3. Runs `INSERT INTO stories_fts(stories_fts) VALUES('optimize')`
4. Closes the connection
5. Logs progress (count of partitions optimized)

Also modify the existing `optimize_fts()` to call `optimize_fts_all(_db_dir)` when in partitioned mode, instead of only iterating `_connections`.

**Verification:** Write test that creates 3 partition DBs, inserts data, calls `optimize_fts_all()`, and verifies all were optimized (no exception raised, FTS search still works).

**Commit:** `feat(db): batch FTS optimize across all partitions`

---

### Task 2: Cross-Partition Search in Shared db.py Module

**Objective:** Move the `connect_multi()` / `ATTACH DATABASE` logic from `scripts/story_db.py` into `src/storybuilder/downloader/db.py` as a first-class API.

**Files:**
- Modify: `src/storybuilder/downloader/db.py`
- Modify: `scripts/story_db.py` (refactor to use new API)
- Test: `tests/test_database.py`

**Approach:** Add to `db.py`:

```python
def search_all_partitions(query: str, *, category: str | None = None,
                          author: str | None = None, date_from: str | None = None,
                          limit: int = 20, db_dir: str | None = None) -> list[dict]:
    """FTS search across all year-partition databases via ATTACH."""
    partition_dir = db_dir or _db_dir
    db_files = sorted(Path(partition_dir).glob("*.db"))
    # Open first as primary, ATTACH rest as aliases
    # Build UNION ALL SELECT ... FROM {alias}.stories s JOIN {alias}.stories_fts fts ...
    # Apply WHERE filters, LIMIT, return list of dicts
```

Then refactor `story_db.py:cmd_search()` to call `search_all_partitions()` instead of its inline logic.

**Verification:** Test creates 2 partition DBs with different stories, calls `search_all_partitions("vampire")`, asserts results from both partitions are returned.

**Commit:** `feat(db): library-level cross-partition FTS search API`

---

## Phase 2: NER Refinement + Entity Search

### Task 3: Extract NER Logic into Shared Module

**Objective:** Move NER logic from root `extract_entities.py` into `src/storybuilder/nlp/ner.py` so it's importable and reusable.

**Files:**
- Create: `src/storybuilder/nlp/__init__.py`
- Create: `src/storybuilder/nlp/ner.py`
- Modify: `extract_entities.py` (thin CLI wrapper importing from nlp.ner)
- Test: `tests/test_ner.py`

**Approach:** `ner.py` exposes:

```python
def load_nlp_model(model: str = "en_core_web_lg", gpu: bool = True) -> spacy.Language:
    """Load spaCy with tagger+parser+ner+merge pipes, GPU optional."""

def extract_entities(doc: spacy.tokens.Doc, allowed_labels: set[str] | None = None) -> list[dict]:
    """Return list of {text, label, frequency} from a processed doc."""

def extract_entities_from_text(text: str, nlp: spacy.Language, ...) -> list[dict]:
    """Convenience: process text then extract."""
```

`extract_entities.py` becomes a thin argparse wrapper calling these functions.

**Verification:** Unit test for `extract_entities()` with mocked spaCy doc containing known PERSON/GPE entities.

**Commit:** `refactor: extract NER logic into storybuilder.nlp.ner module`

---

### Task 4: Add Entities Table to Main Stories DB

**Objective:** Add an `entities` table to the main stories DB schema (alongside the existing `stories` + `stories_fts` tables) so entities can be queried alongside stories.

**Files:**
- Modify: `src/storybuilder/downloader/db.py` (schema in `init_db`)
- Modify: `src/storybuilder/nlp/ner.py` (add `store_entities()` function)
- Test: `tests/test_database.py`, `tests/test_ner.py`

**Approach:** Add to the schema in `db.py`:

```sql
CREATE TABLE IF NOT EXISTS story_entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_path TEXT NOT NULL,
    entity_text TEXT NOT NULL,
    entity_label TEXT NOT NULL,
    frequency INTEGER DEFAULT 1,
    UNIQUE(story_path, entity_text, entity_label)
);
CREATE INDEX IF NOT EXISTS idx_entity_text ON story_entities(entity_text);
CREATE INDEX IF NOT EXISTS idx_entity_label ON story_entities(entity_label);
```

Note: This must be added to **each partition DB** as well (the schema init runs per-partition already).

**Verification:** Test inserts a story + entities, queries by entity_text, verifies correct story_path returned.

**Commit:** `feat(db): add story_entities table to partition schema`

---

### Task 5: Entity-Based Story Search

**Objective:** Add a `search_by_entity()` function and CLI subcommand to find stories by character name, location, etc.

**Files:**
- Modify: `src/storybuilder/downloader/db.py`
- Modify: `scripts/story_db.py` (add `entity` subcommand)
- Test: `tests/test_database.py`

**Approach:** In `db.py`:

```python
def search_by_entity(entity_text: str, *, entity_label: str | None = None,
                     limit: int = 20, db_dir: str | None = None) -> list[dict]:
    """Search story_entities across partitions, join with stories for metadata."""
```

In `story_db.py`, add subcommand:
```
python scripts/story_db.py entity "Mark" --label PERSON --limit 10
```

**Verification:** Test inserts entities into 2 partitions, searches by entity name, asserts cross-partition results.

**Commit:** `feat(db): entity-based story search across partitions`

---

## Phase 3: TTS Engine Enhancements

### Task 6: Prompt Composer Agent — Multi-Engine Support

**Objective:** Extend the existing ADK agent to generate prompts compatible with multiple TTS engines (Gemini, Cartesia), abstracting engine-specific voice matrices and format constraints.

**Files:**
- Modify: `src/storybuilder/agents/tts_prompt_crafter/agent.py`
- Modify: `src/storybuilder/agents/tts_prompt_crafter/prompts.py`
- Create: `src/storybuilder/agents/tts_prompt_crafter/engine_configs.py`
- Test: `tests/test_agent_tools.py`

**Approach:** Create `engine_configs.py` with:

```python
ENGINE_CONFIGS = {
    "gemini": {
        "voice_matrix": {...},  # M4M voice matrix from SKILL.md
        "max_voices": 2,
        "preamble_template": "...",  # existing Gemini preamble
        "format": "markdown",
    },
    "cartesia": {
        "voice_matrix": {...},  # Cartesia voice IDs mapped from names
        "max_voices": 2,
        "preamble_template": "...",
        "format": "markdown",
    },
}
```

The scene_writer agent's prompt receives the target engine as context and selects the appropriate voice matrix and preamble.

**Verification:** Test that agent generates prompts with correct voice names for each engine given the same story input.

**Commit:** `feat(agent): multi-engine TTS prompt support (Gemini + Cartesia)`

---

### Task 7: TTS Output Validation Framework

**Objective:** Build a validation module that checks generated audio files against the source prompt for basic correctness.

**Files:**
- Create: `src/storybuilder/genai/validator.py`
- Test: `tests/test_validator.py`

**Approach:** Start with achievable validations (not full audio content analysis):

```python
class TTSValidationResult:
    audio_exists: bool          # .wav file exists and > 0 bytes
    audio_duration_ok: bool     # duration > 1 second
    parseable_prompt: bool      # source .md parsed successfully
    speaker_count_ok: bool      # prompt has ≤ 2 speakers
    transcript_present: bool    # prompt contains TRANSCRIPT section

def validate_tts_output(wav_path: str, prompt_path: str) -> TTSValidationResult:
    """Run all validation checks on a generated TTS audio file."""
```

Future iterations can add waveform analysis (silence detection, speaker diarization) — but start with structural checks that catch obvious failures.

**Verification:** Test with a valid WAV + prompt pair (all pass), missing WAV (fail), 0-byte WAV (fail), prompt without TRANSCRIPT (fail).

**Commit:** `feat(genai): TTS output validation framework`

---

### Task 8: Integrate Validation into GenAI Client

**Objective:** Wire the validator into `process_directory()` so failed generations are flagged and optionally retried.

**Files:**
- Modify: `src/storybuilder/genai/client.py`
- Test: `tests/test_genai.py`

**Approach:** After generating each WAV in `process_directory()`:
1. Call `validate_tts_output(wav_path, prompt_path)`
2. If any critical check fails, log WARNING with details
3. Add `--validate` flag to the CLI to enable validation (off by default initially)
4. Add `--retry-on-failure N` flag to retry failed validations up to N times

**Verification:** Mock the API call to produce a 0-byte file, assert validation catches it and logs warning.

**Commit:** `feat(genai): integrate TTS validation into generation pipeline`

---

### Task 9: Cartesia TTS Client — Tests and Polish

**Objective:** The Cartesia client exists at `src/storybuilder/genai/cartesia_client.py` but lacks integration tests. Add tests for the full pipeline and fix any gaps.

**Files:**
- Modify: `tests/test_cartesia.py`
- Modify: `src/storybuilder/genai/cartesia_client.py` (minor fixes if needed)

**Approach:** Add tests for:
1. `generate_segment_audio()` — mock the HTTP call, verify WAV bytes are correct
2. `process_directory_cartesia()` — mock generation, verify concatenation and file output
3. Error handling: API timeout, invalid voice ID, empty transcript

**Verification:** `uv run pytest tests/test_cartesia.py -v` — all tests pass.

**Commit:** `test(cartesia): add integration tests for Cartesia TTS client`

---

## Phase 4: UI (Streamlit Story Database Viewer)

### Task 10: Scaffold Streamlit UI App

**Objective:** Create a Streamlit app for browsing and searching the story database.

**Files:**
- Create: `src/storybuilder/ui/__init__.py`
- Create: `src/storybuilder/ui/app.py`
- Create: `src/storybuilder/ui/search_page.py`
- Create: `src/storybuilder/ui/stats_page.py`
- Modify: `pyproject.toml` (add streamlit dependency, optional group)

**Approach:** Multi-page Streamlit app:

- **Page 1: Search** — FTS text input, filters (category dropdown, date range, author text), results table with snippets, click to view full story
- **Page 2: Browse** — Paginated story list with sort options
- **Page 3: Stats** — Story counts by category, date histogram, word count distribution

Uses the `search_all_partitions()` and `search_by_entity()` functions from Phase 1–2.

Run via: `streamlit run src/storybuilder/ui/app.py`

**Verification:** Manual smoke test — app starts, search returns results, stats page renders charts.

**Commit:** `feat(ui): scaffold Streamlit story database viewer`

---

### Task 11: Export to Markdown

**Objective:** Add export functionality to the UI and CLI.

**Files:**
- Modify: `scripts/story_db.py` (enhance `get --export`)
- Modify: `src/storybuilder/ui/search_page.py` (export button)

**Approach:** The CLI already has `get --export` (observed in `story_db.py`). Enhance it to support:
- Single story export to `.md` with full header
- Batch export from search results to a zip of `.md` files

In the Streamlit UI, add a download button on search results.

**Verification:** Export a story via CLI, verify `.md` content matches DB content.

**Commit:** `feat(ui): add markdown export to UI and CLI`

---

## Phase 5: Codebase Cleanup

### Task 12: Move Root Scripts into Package

**Objective:** Move standalone root scripts into the `src/storybuilder/` package as proper submodules.

**Files:**
- Create: `src/storybuilder/nlp/sentiment.py` (from `analyze_sentiment.py`)
- Create: `src/storybuilder/nlp/embeddings.py` (from `generate_embeddings.py`)
- Create: `src/storybuilder/nlp/similarity.py` (from `find_similar.py`)
- Create: `src/storybuilder/analysis/narrative_arcs.py` (from `compare_narratives.py`, `visualize_arcs.py`)
- Create: `src/storybuilder/analysis/tsne_viz.py` (from `visualize_tsne.py`)
- Delete: `main.py` (stub, replaced by `src/storybuilder/__main__.py`)

**Approach:** For each script:
1. Move logic into the appropriate submodule
2. Replace root script with a thin wrapper that imports and calls the module
3. Update `pyproject.toml` `[project.scripts]` entry points if needed
4. Run `uv run pytest` to verify nothing breaks

Keep root-level thin wrappers for backward compatibility (e.g., `extract_entities.py` just imports and calls `nlp.ner.main()`).

**Verification:** `uv run pytest` passes. All root scripts still work as before.

**Commit:** `refactor: move root scripts into storybuilder package modules`

---

### Task 13: Deduplicate Tests

**Objective:** Remove duplicated tests in `test_split_prompts.py` that duplicate `test_downloader.py` and `test_genai.py`.

**Files:**
- Modify: `tests/test_split_prompts.py`

**Approach:** Identify and remove test methods in `test_split_prompts.py` that are exact copies of tests in other files. Keep only the tests unique to the split_prompts module.

**Verification:** `uv run pytest` — all tests pass, no duplicate test names.

**Commit:** `test: deduplicate tests across test files`

---

## Dependencies and Ordering

```
Phase 1 (DB) ────────> Phase 2 (NER, depends on db.py changes)
                                  │
Phase 3 (TTS) ────────> Phase 4 (UI, depends on search + entity APIs)
                                  │
Phase 5 (Cleanup) ────> Last (after all features are stable)
```

Phases 1 and 3 are independent and can be worked in parallel.
Phase 2 depends on Phase 1 (cross-partition search API).
Phase 4 depends on Phases 1 + 2 (UI uses the new APIs).
Phase 5 should be done last.

## Risks and Tradeoffs

- **Cross-partition search performance:** ATTACHing 37 DBs and UNION ALL may be slow for large queries. Mitigation: limit ATTACH to year range relevant to the query, or add `--year-range` filter.
- **NER model accuracy:** spaCy `en_core_web_lg` has known issues with fiction text (unusual names, dialogue). Mitigation: add a custom entity mergeer or allowlist for known character names from story metadata.
- **TTS validation scope:** Structural checks (file exists, duration > 1s) are weak. Full audio content analysis (speaker diarization, transcription verification) is a separate large project. Mark it as future work.
- **Streamlit dependency:** Adds a heavy optional dependency. Keep it in an `[ui]` optional group in pyproject.toml.
- **Root script cleanup:** External tooling or CI may reference root scripts. Keep thin wrappers at root level for backward compatibility.
