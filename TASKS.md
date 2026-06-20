# Tasks

## Active

### Phase 1: Database Improvements (from 2026-06-18 Implementation Plan)

- [ ] **Batch FTS Optimize for All Partitions** (Task 1) #ISSUE
  - [] Implement `optimize_fts_all(db_dir)` in `src/storybuilder/downloader/db.py` to optimize all partition databases.
  - [] Modify existing `optimize_fts()` to call this in partitioned mode.
  - [] Add tests in `tests/test_database.py`.
  - [] *Commit:* `feat(db): batch FTS optimize across all partitions`
- [ ] **Cross-Partition Search in Shared db.py Module** (Task 2) #ISSUE
  - [] Move the ATTACH/connect_multi logic to `src/storybuilder/downloader/db.py:search_all_partitions`.
  - [] Refactor `scripts/story_db.py` to use new API.
  - [] Add tests in `tests/test_database.py`.
  - []*Commit:* `feat(db): library-level cross-partition FTS search API`

### Phase 2: NER Refinement + Entity Search (from 2026-06-18 Implementation Plan)

- [ ] **Extract NER Logic into Shared Module** (Task 3)
  - [] Extract logic from root `extract_entities.py` to `src/storybuilder/nlp/ner.py`.
  - [] Make `extract_entities.py` a thin CLI wrapper.
  - [] Add tests in `tests/test_ner.py`.
  - []*Commit:* `refactor: extract NER logic into storybuilder.nlp.ner module`
- [ ] **Add Entities Table to Main Stories DB** (Task 4)
  - [] Add `story_entities` table to main/partition DB schema.
  - [] Implement `store_entities()` in `src/storybuilder/nlp/ner.py`.
  - [] Add tests.
  - []*Commit:* `feat(db): add story_entities table to partition schema`
- [ ] **Entity-Based Story Search** (Task 5)
  - [] Add `search_by_entity()` to `db.py`.
  - [] Add `entity` subcommand to `scripts/story_db.py`.
  - [] Add tests.
  - []*Commit:* `feat(db): entity-based story search across partitions`

### Phase 3: TTS Engine Enhancements (from 2026-06-18 Implementation Plan)

- [ ] **Prompt Composer Agent — Multi-Engine Support** (Task 6) #TASK
  - []Extend ADK agent for engine-specific voice matrices (Gemini, Cartesia).
  - []Modify `src/storybuilder/agents/tts_prompt_crafter/agent.py` and `prompts.py`.
  - []Create `engine_configs.py`.
  - []*Commit:* `feat(agent): multi-engine TTS prompt support (Gemini + Cartesia)`
- [ ] **TTS Output Validation Framework** (Task 7) #FIXME
  - []Create `src/storybuilder/genai/validator.py` with `validate_tts_output()`.
  - [] Validate WAV existence, duration, and prompt structure.
  - [] Add tests in `tests/test_validator.py`.
  - []*Commit:* `feat(genai): TTS output validation framework`
- [ ] **Integrate Validation into GenAI Client** (Task 8)
  - [] Call validator in `process_directory()` in `src/storybuilder/genai/client.py`.
  - [] Add `--validate` and `--retry-on-failure N` flags.
  - []*Commit:* `feat(genai): integrate TTS validation into generation pipeline`
- [ ] **Cartesia TTS Client — Tests and Polish** (Task 9) #TASK
  - [] Add tests for `generate_segment_audio`, `process_directory_cartesia`, and error handling in `tests/test_cartesia.py`.
  - [] Clean up `src/storybuilder/genai/cartesia_client.py`.
  - []*Commit:* `test(cartesia): add integration tests for Cartesia TTS client`

### Phase 4: UI & Markdown Export (from 2026-06-18 Implementation Plan)

- [x] **Create interactive Streamlit dashboard** / **Scaffold Streamlit UI App** (Task 10) (2026-06-19)
  - Browsing, searching, and stats in `scripts/dashboard.py`.
- [x] **Add a Markdown export function** / **Export to Markdown** (Task 11) (2026-06-19)
  - Export single/batch stories to `.md`/zip via UI and CLI.
- [x] **Implement named entity filters** by joining searches with `nlp_analysis.db`. (2026-06-19)
- [x] **Integrate FTS5 full-text query** with highlighted match snippets across year partitions. (2026-06-19)
- [x] **Add a dynamic statistics tab** with interactive Plotly distribution charts. (2026-06-19)
- [x] **Add a persistent Favorites & Tagging system** saving to `stories/db/dashboard_metadata.db`. (2026-06-19)
- [x] Full text search does not consider the title. #ISSUE (2026-06-20)
- [x] Multi-chapter stories are not linked in any way, making it hard to find a series or the first or last chapter. #ISSUE (2026-06-20)
- [x] Author filter does not work. #ISSUE (2026-06-20)
- [x] Category filter does not work. #ISSUE (2026-06-20)
- [x] Many stories from 2026 are in multiple identical copies [Weird distribution](newplot.png) #ISSUE (2026-06-20)
- [x] Selecting a story does not transition to reading panel, only darkens the screen. #ISSUE (2026-06-20)
- [x] Entity filter does not work. #ISSUE (2026-06-20)
- [x] It would be nice to see a search result score next to each story. #IDEA (2026-06-20)

### Phase 5: Codebase Cleanup (from 2026-06-18 Implementation Plan)

- [x] **Move Root Scripts into Package** (Task 12) (2026-06-19)
  - [] Move root scripts (sentiment, embeddings, similarity, arcs, tsne) into `src/storybuilder/` package.
- [ ] **Deduplicate Tests** (Task 13)
  - [] Remove duplicate tests in `tests/test_split_prompts.py` that copy `test_downloader.py` and `test_genai.py`.
  - []*Commit:* `test: deduplicate tests across test files`

## Someday

- [ ] **Add an ElevenLabs TTS client** #TASK
- [ ] **Elevate the TTS output into a high-end, immersive audio drama** (often referred to as an "enhanced audiobook" or "binaural audio play") #TASK
  - [ ] **Gather a targeted collection of sound assets in your DAW** See `stories/text/output/i_came_during_tryouts/daw.md` for an example. #IDEA
  - [ ] **Implement advanced audio engineering techniques** to create a polished, professional final product #IDEA

## XAI TTS API Skill Implementation

- [ ] Test the benchmark properly using the `benchmark.py` script using the provided evals and sub-agents. #LATER
- [ ] Update the review.html to display the results properly. If not good , go back to LLM and ask it to fix it. #LATER

## Done

- [x] ~~Clean up single script files in the root directory and move the useful scripts to appropriate submodules.~~ (2026-06-19)
- [x] ~~Implement story scraper to scrape stories from nifty.org~~ (2026-06-19)
- [x] ~~Implement SQL database schema and database management module to store stories.~~ (2026-06-19)
- [x] ~~Add FTS5 to the database schema.~~ (2026-06-19)
- [x] ~~Partition database by year.~~ (2026-06-19)
- [x] ~~Implement basic named entity recognition to extract character names, locations, and other entities from stories.~~ (2026-06-19)
- [x] ~~Implement a prompt composer agent to compose prompts for TTS engine.~~ (2026-06-19)
- [x] ~~Merge QWEN.md into AGENTS.md~~ (2026-06-19)
