# AGENTS.md

Non-obvious repository knowledge, workflows, architecture, and operational gotchas for StoryBuilder.

## Project & Stack Overview

StoryBuilder is a Python toolkit for narrative fiction scraping, SQLite/FTS5 indexing, sentiment/entity/embedding analysis, Streamlit browsing, and multi-provider TTS (Gemini, Cartesia). An xAI TTS skill exists under `.agent/skills/`; there is no `xaiapi/` package in `src/`.

| Layer | Technology & Libraries |
| --- | --- |
| Language & Tooling | Python 3.12+, `uv` package manager |
| NLP & Vectors | spaCy (`en_core_web_sm`, `en_core_web_lg`), HuggingFace, sentence-transformers, ChromaDB |
| Audio / TTS | Google GenAI, Cartesia (`Cartesia-Version: 2026-03-01`) |
| Data & UI | SQLite (FTS5), optional S3/GCS upload, Streamlit dashboard |
| Agents | Google ADK (`tts_prompt_crafter`, YAML `cartesia_tts_prompt_crafter`) |

Console scripts: `downloader` → `storybuilder.downloader.cli:main`; `genai-tts` → `storybuilder.genai.tts:main`; `story-import` → `storybuilder.db_tools.import_to_sqlite:main`; `story-db` → `storybuilder.db_tools.story_db:main`. There is no `storybuilder` entrypoint.

### Structure & Layout

- `src/storybuilder/` — `downloader/`, `analysis/`, `genai/`, `dashboard/`, `agents/`, `db_tools/`, `utils/`. Direct `__main__` execution may insert the project root on `sys.path`.
- `src/storybuilder/db_tools/` — SQLite import (`story-import`) and FTS search (`story-db`) console-script CLIs.
- `scripts/` — `dashboard.py` (Streamlit launcher).
- `tests/` — `unittest`-based suite run via `uv run pytest`.
- `.agent/skills/` — Workflow docs and skill references.
- `stories/text/` — default downloader output. `nifty_stories/` is a legacy path still used as a default in some analysis CLIs.

Do not look for `src/storybuilder/{cartesia,xaiapi,bedrock}` or `src/prompts/` — those paths are gone.

---

## Workflows & Essential Commands

### 1. Environment Setup

- **Dependencies**: `uv sync --all-extras --dev`
- **spaCy Models**: `uv run python -m spacy download en_core_web_sm && uv run python -m spacy download en_core_web_lg`
- **API Keys (`.env`)**: `GEMINI_API_KEY` (rotate with `GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, … on quota limits), `CARTESIA_API_KEY`. Optional: `HF_TOKEN`, AWS/GCS creds for uploads, `STORYBUILDER_LIVE_API=1` for live integration tests.

### 2. Downloader (Nifty Scraper & Fetcher)

- **CLI**: `downloader --category gay --start-date 1990-01-01 --end-date 2025-12-31 --output-dir stories/text --socks5-proxy 192.168.2.10:37459 --rotate-on-refusal --max-scraping 5 --max-workers 5` (or `python -m storybuilder.downloader.cli`).
- **Flags**: `--force` (bypass cache early-stop), `--delay` (inter-request sleep; **0.01s** default in parser, help text still says 1.0s), `--db` (default `stories/db`; empty string disables insert), `--s3-bucket` / `--gcs-bucket`.
- **Help-text drift**: `--output-dir` default is `stories/text` (help still says `nifty_stories`); `--max-workers` default is 5 (help still says 1).
- **Subsystem & Gotchas**:
  - Requires `pysocks` for SOCKS5 proxies. IP rotation (`rotate_windscribe_ip`) triggers on HTTP 403/429/503 or network exceptions when `ENABLE_ROTATION` is set.
  - 2-phase pipeline: scrape listing targets then fetch concurrently (`ThreadPoolExecutor`).
  - Cache safety: early stop is safe ONLY if `is_complete` OR `min_cached_date <= start_date` (`metadata_cache.json`). Multi-chapter "Dir" folders use a separate `folder_date` key. Thread lock `seen_folders` prevents duplicate multi-chapter folder processing.
  - Date parsing (`parse_nifty_date`): imputes missing years from reference date; rolls future dates to prior year. Fallback regex handles bare "Jun 6".
  - Bulk-touch sentinel: archive migrations rewrite file mtimes (Jun 2025–Jun 2026 event touched ~163k stories). `db.flag_bulk_touched_dates()` runs automatically at CLI end and resets `publication_date` to `1970-01-01` for any date with >150 stories/day (organic max ~102). ~80% of flagged rows carry a recoverable usenet `Date:` header inside `content`: `story-db redate` (→ `db.redate_from_content_headers()`) restores them (recovered 131,769/162,996 = 80.8%); header-less rows stay at the epoch sentinel.
  - Output header: prepend `=====` title/author/date/url header. Duplicate target files across subcategories are copied via `shutil.copy2` after first fetch.

### 3. Database Import & Search (SQLite FTS5)

- **Import**: `story-import [--db stories/stories.db] [--limit N] [--force]`
  - Idempotent via `UNIQUE(path)`. Parses two-line `=====` header and `Name <email>` authors.
  - FTS5 external content virtual table is kept in sync **exclusively** by 3 `AFTER` triggers (`INSERT`, `DELETE`, `UPDATE`). Direct table edits desync search.
- **Search CLI**: `story-db --db stories/stories.db search "query" [--author X] [--category Y] [--date-from ...] [--limit 20] [--snippets]` (subcommands: `search`, `get`, `list`, `stats`, `redate`, `refetch`, `interpolate`).
- **Date provenance**: `stories.date_source` records how `publication_date` was obtained. Exact tier: `listing` (scrape mtime), `content_header` (usenet `Date:` parsed from content — includes the Sep 2026 refetch recoveries), `refetch_header` (stamped by future `story-db refetch` runs). Estimate tier: `interpolated` / `extrapolated` (sibling-chapter estimates). Sentinel: `unresolved` (epoch, bulk-touch victim). Column added via O(1) `ALTER TABLE ... DEFAULT 'listing'` migration in `_migrate_schema`; stamped by every write path (`insert_story`, flag/redate/refetch/interpolate); `date_source` is NOT FTS-indexed, so provenance/date-only bulk updates bypass the `stories_au` trigger.
- **Epoch-date recovery pipeline**: `story-db redate` (usenet `Date:` headers already in content) → `story-db refetch` (extension-less URLs now served as text/plain WITH headers; also enriches content/title/author) → `story-db interpolate` (estimates remaining chapter dates from dated siblings by chapter_num; linear interpolation / median-pace extrapolation). Touched listing dates carry NO chronological signal — never use them as estimators. Maintenance commands auto-upload `stories.db` to `gs://nifty-index` when they write changes (after WAL checkpoint via `close_db`); skip with `--no-upload`, retarget with `--gcs-bucket`.
- Downloader and dashboard default to a `stories/db` directory (SQLModel `Story`).

### 4. Analysis & Vector Pipeline

Execute in order (argparse + GPU-first `--gpu` flag, idempotent skip):

1. `python -m storybuilder.analysis.extract_entities --stories-dir stories/text --gpu`
2. `python -m storybuilder.analysis.analyze_sentiment --stories-dir stories/text --gpu`
3. `python -m storybuilder.analysis.generate_embeddings --stories-dir stories/text` (populates dual Chroma collections: `story_chunks` + `story_averages`)
4. `python -m storybuilder.analysis.find_similar "path/to/story.txt"`
5. `python -m storybuilder.analysis.visualize_arcs --story "slug" --window 100`
6. `python -m storybuilder.analysis.compare_narratives --clusters 4`
7. `python -m storybuilder.analysis.visualize_tsne --perplexity 1000`
8. `python -m storybuilder.genai.test_voices`

Several analysis CLIs still default `--stories-dir` to `nifty_stories` or `test_stories`. Pass `stories/text` explicitly unless you have those trees.

### 5. Dashboard

```bash
streamlit run scripts/dashboard.py
```

Pages: Search & Explorer, Read Story, Favorites & Tags, Archive Stats.

Env: `STORYBUILDER_DB_DIR` (default `stories/db`), `STORYBUILDER_NLP_DB_PATH`, `STORYBUILDER_META_DB_PATH`, `DASHBOARD_DEV_MODE=true` (reload modules each run).

### 6. TTS Prompt Crafter & Generation

- **Prompt Splitter**: `python .agent/skills/tts-prompt-crafter/scripts/split_prompts.py <dir-containing-*-scene*.md>`
  - Archives original `*-scene*.md` files into zero-padded `01-part.md`, `02-part.md`, etc. Chunks on 3rd unique speaker or >1800 characters.
  - Mandatory header: must start with exact literal `# SYSTEM PREAMBLE: Synthesize speech ONLY for the transcripts under the #### TRANSCRIPT headers. ...` (prevents model reading structural headings aloud).
  - Schema structure: `# AUDIO PROFILE`, `### THE SCENE`, `### DIRECTOR'S NOTES` (`Style: - Name (Voice: VoiceName): desc`), `### SAMPLE CONTEXT`, `#### TRANSCRIPT`.
  - Emotion tags: inline English only (`[whispers]`). Adjacent tags like `[sighs][whispers]` trigger API parse errors (splitter emits warning). Bracket symmetry is strictly validated.
- **Gemini TTS Client**: `genai-tts --dir stories/<slug>` (or `python -m storybuilder.genai.client --dir ...`)
  - Uses `client.interactions.create()`. Skips existing `.wav`. Retries 429 quota with 15s backoff, 2s sleep between files. Uses `previous_interaction_id` for stateful voice continuity.
  - Voice constraints: max 2 voices per call. Single-speaker prompts are padded with `{"speaker": "Dummy", "voice": "Puck"}` to avoid HTTP 400. No-speaker fallback: `Kore`.
- **Cartesia TTS**: `python -m storybuilder.genai.cartesia_client --dir ... --rate 24000`. Requires `CARTESIA_API_KEY`. Fetch `https://docs.cartesia.ai/llms.txt` before changing API usage. Default header: `Cartesia-Version: 2026-03-01`.
- **ADK agent**: `src/storybuilder/agents/tts_prompt_crafter/`. Tools resolve story names under `stories/text` (absolute paths also allowed). Vertex memory bank (`storage-499607`, engine `8434441657599918080`) and OTEL `localhost:4318` are hardcoded in `agent.py`. Session DB: `stories/db/tts_prompt_crafter.db`.

---

## Conventions & Integration

### Code & Test Standards

- **Testing**: `uv run pytest` (`unittest.TestCase` modules under `tests/`). Markers: `slow`, `adk_eval`, `agentic`, `integration`. Live APIs: `STORYBUILDER_LIVE_API=1`. Uses `unittest.mock.patch` for network/cache isolation and `tempfile.mkdtemp()`.
- **Style Rules**: Python 3.12+ type hints required. Use `argparse` for all CLIs. Threading lock objects use `_lock` suffix (`print_lock`, `cache_lock`, `seen_folders_lock`).

### Git

- Branch off `main`. Use conventional commit prefixes (`feat:`, `fix:`, `docs:`).
- Changelog: append to `CHANGELOG.md` following Added/Changed/Removed/Fixed.
- `tasks/TASKS.md` tracks product work. There is no `.github/workflows/auto-linear.yml` in this tree.
