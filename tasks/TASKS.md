# Tasks

## Active

### Priority

- [x] **Reduce the number of audio files generated during tests** Not more than 2-3 files generated, if absolutely necessary.  - #ISSUE

### Testability and Agent Benchmarks

- [ ] **Improve test coverage** Currently at 50%. Need to get to at least 80%. #TASK
- [ ] **Add TTS validation pipeline** - implement a comprehensive validation system for TTS output. #TASK
- [ ] **Add benchmarks for all agents** - implement benchmarks for all agents. #TASK

### Phase 1: Unified Streamlit Dashboard

- [x] **Create interactive Streamlit dashboard** (`scripts/dashboard.py`) to search and view stories. (2026-06-19)
- [x] **Implement named entity filters** by joining searches with `nlp_analysis.db`. (2026-06-19)
- [x] **Integrate FTS5 full-text query** with highlighted match snippets across year partitions. (2026-06-19)
- [x] **Add a dynamic statistics tab** with interactive Plotly distribution charts. (2026-06-19)
- [x] **Add a persistent Favorites & Tagging system** saving to `stories/db/dashboard_metadata.db`. (2026-06-19)
- [x] **Add a Markdown export function** to download selected stories/search results. (2026-06-19)

### Phase 1.1: Story Discovery Enhancements

- [ ] **Refine named entity recognition** - improve extraction of relationships and higher-quality entities.
- [ ] **Add an interactive visualization** to the dashboard to visualize the relationships between entities.

### Phase 2: TTS & Audio Enhancements

- [ ] **Add a Cartesia TTS client** - wire up Cartesia support alongside the existing TTS flow. #TASK
- [ ] **Improve TTS output validation** - verify audio generation, voice assignment, dialogue coverage, sound effects, and performance adherence. #FIXME

## Waiting On

- [x] **Optimize FTS across year partitions** - scan all year databases and batch-run `optimize_fts()` or the equivalent PRAGMA optimization path. #ISSUE
- [x] **Support cross-partition search** - dynamically attach partition files with `ATTACH DATABASE` when performing global queries. #ISSUE

## Someday

- [ ] **Add an ElevenLabs TTS client** #TASK
- [ ] **Make the prompt composer engine-agnostic** - generate prompts for multiple TTS engines. #TASK

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
- [x] ~~Migrate database layer to a SQLModel monolithic architecture~~ (2026-07-10) — Deprecated year-partitioning, consolidated all records into `stories.db`, and replaced raw SQL with SQLModel `select()`/`execute_query()`/`search_stories()` (see `tasks/monolithic_db_plan.md`).
- [x] ~~Modularize the Streamlit dashboard~~ (2026-07-15) — Split the 875-line `scripts/dashboard.py` monolith into `src/storybuilder/dashboard/` (`config.py`, `data.py`, `ui/sidebar.py`, `pages/`), leaving `scripts/dashboard.py` as a thin launcher (see `tasks/dashboard_refactor_draft.md`).
