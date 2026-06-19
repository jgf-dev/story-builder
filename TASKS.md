# Tasks

## Active

- [ ] **Implement a story search function** - search stories based on named entities.
- [ ] **Implement a story database viewer** - let the user search stories with a prompt or filter by date, categories, and similar metadata.
- [ ] **Add an export function** - export stories to a markdown file.
- [ ] **Add a statistics tab** - show story counts by date, categories, genre, word count, named entities, and similar metrics.
- [ ] **Improve TTS output validation** - verify audio generation, voice assignment, dialogue coverage, sound effects, and performance adherence.
- [ ] **Add a Cartesia TTS client** - wire up Cartesia support alongside the existing TTS flow.

## Waiting On

- [ ] **Optimize FTS across year partitions** - scan all year databases and batch-run `optimize_fts()` or the equivalent PRAGMA optimization path.
- [ ] **Support cross-partition search** - dynamically attach partition files with `ATTACH DATABASE` when performing global queries.

## Someday

- [ ] **Add an ElevenLabs TTS client**
- [ ] **Make the prompt composer engine-agnostic** - generate prompts for multiple TTS engines.
- [ ] **Refine named entity recognition** - improve extraction of relationships and higher-quality entities.
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
