# Tasks

## Active

### Phase 1: Unified Streamlit Dashboard

- [x] **Create interactive Streamlit dashboard** (`scripts/dashboard.py`) to search and view stories. (2026-06-19)
- [x] **Implement named entity filters** by joining searches with `nlp_analysis.db`. (2026-06-19)
- [x] **Integrate FTS5 full-text query** with highlighted match snippets across year partitions. (2026-06-19)
- [x] **Add a dynamic statistics tab** with interactive Plotly distribution charts. (2026-06-19)
- [x] **Add a persistent Favorites & Tagging system** saving to `stories/db/dashboard_metadata.db`. (2026-06-19)
- [x] **Add a Markdown export function** to download selected stories/search results. (2026-06-19)
- [ ] **Refine named entity recognition** - improve extraction of relationships and higher-quality entities.


### Phase 2: TTS & Audio Enhancements

- [ ] **Add a Cartesia TTS client** - wire up Cartesia support alongside the existing TTS flow.
- [ ] **Improve TTS output validation** - verify audio generation, voice assignment, dialogue coverage, sound effects, and performance adherence.

## Waiting On

- [ ] **Optimize FTS across year partitions** - scan all year databases and batch-run `optimize_fts()` or the equivalent PRAGMA optimization path.
- [ ] **Support cross-partition search** - dynamically attach partition files with `ATTACH DATABASE` when performing global queries.

## Someday

- [ ] **Add an ElevenLabs TTS client**
- [ ] **Make the prompt composer engine-agnostic** - generate prompts for multiple TTS engines.

- [ ] **Elevate the TTS output into a high-end, immersive audio drama** (often referred to as an "enhanced audiobook" or "binaural audio play")
  - [ ] **Gather a targeted collection of sound assets in your DAW** See `stories/text/output/i_came_during_tryouts/daw.md` for an example.
  - [ ] **Implement advanced audio engineering techniques** to create a polished, professional final product

## Done

- [x] ~~Clean up single script files in the root directory and move the useful scripts to appropriate submodules.~~ (2026-06-19)
- [x] ~~Implement story scraper to scrape stories from nifty.org~~ (2026-06-19)
- [x] ~~Implement SQL database schema and database management module to store stories.~~ (2026-06-19)
- [x] ~~Add FTS5 to the database schema.~~ (2026-06-19)
- [x] ~~Partition database by year.~~ (2026-06-19)
- [x] ~~Implement basic named entity recognition to extract character names, locations, and other entities from stories.~~ (2026-06-19)
- [x] ~~Implement a prompt composer agent to compose prompts for TTS engine.~~ (2026-06-19)
- [x] ~~Merge QWEN.md into AGENTS.md~~ (2026-06-19)
