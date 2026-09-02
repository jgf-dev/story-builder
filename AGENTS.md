# AGENTS.md

Non-obvious repository knowledge, workflows, architecture, and operational gotchas for StoryBuilder.

## Project & Stack Overview

StoryBuilder is a Python toolkit for narrative fiction scraping, SQLite/FTS5 indexing, sentiment/entity/embedding analysis, and multi-provider TTS generation (Gemini, Cartesia, xAI).

| Layer | Technology & Libraries |
|---|---|
| Language & Tooling | Python 3.12+, `uv` package manager |
| NLP & Vectors | spaCy (`en_core_web_sm`, `en_core_web_lg`), HuggingFace, sentence-transformers, ChromaDB |
| Audio / TTS | Google GenAI (Interactions API), Cartesia, xAI Grok |
| Data & Cloud | SQLite (FTS5), AWS Bedrock AgentCore / Boto3 |

### Structure & Layout
- `src/storybuilder/` — Core package (`downloader/`, `genai/`, `cartesia/`, `xaiapi/`, `bedrock/`, `utils/`, `analysis/`). Uses `sys.path` hacks for direct module execution.
- `src/storybuilder/db_tools/` — SQLite import (`story-import`) and FTS search (`story-db`) console-script CLIs.
- `tests/` — `unittest`-based suite run via `uv run pytest`.
- `src/prompts/` & `.agent/skills/` — Prompt templates, splitter script (`split_prompts.py`), and workflow docs.
- `stories/` & `nifty_stories/` — Output story text files and archived audio parts.

---

## Workflows & Essential Commands

### 1. Environment Setup
- **Dependencies**: `uv sync --all-extras --dev`
- **spaCy Models**: `python -m spacy download en_core_web_sm && python -m spacy download en_core_web_lg`
- **API Keys (`.env`)**: Requires `GEMINI_API_KEY` (rotate with `GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, etc. on quota limits), `CARTESIA_API_KEY`, `XAI_API_KEY`, and AWS credentials.

### 2. Downloader (Nifty Scraper & Fetcher)
- **CLI**: `storybuilder --category gay --start-date 1990-01-01 --end-date 2025-12-31 --output-dir nifty_stories --socks5-proxy 192.168.2.10:37459 --rotate-on-refusal --max-scraping 5 --max-workers 5` (or `python -m storybuilder.downloader.cli`).
- **Flags**: `--force` (bypass cache early-stop), `--delay` (inter-request sleep; 0.01s default in parser, 1.0s in help text).
- **Subsystem & Gotchas**:
  - Requires `pysocks` for SOCKS5 proxies. IP rotation (`rotate_windscribe_ip`) triggers on HTTP 403/429/503 or network exceptions when `ENABLE_ROTATION` is set.
  - 2-phase pipeline: Scrape listing targets then fetch concurrently (`ThreadPoolExecutor`).
  - Cache safety: Early stop is safe ONLY if `is_complete` OR `min_cached_date <= start_date` (`metadata_cache.json`). Multi-chapter "Dir" folders use a separate `folder_date` key. Thread lock `seen_folders` prevents duplicate multi-chapter folder processing.
  - Date parsing (`parse_nifty_date`): Imputes missing years from reference date; rolls future dates to prior year. Fallback regex handles bare "Jun 6".
  - Output header: Prepend `=====` title/author/date/url header. Duplicate target files across subcategories are copied via `shutil.copy2` after first fetch.

### 3. Database Import & Search (SQLite FTS5)
- **Import**: `story-import [--db stories/stories.db] [--limit N] [--force]`
  - Idempotent via `UNIQUE(path)`. Parses two-line `=====` header and `Name <email>` authors.
  - FTS5 external content virtual table is kept in sync **exclusively** by 3 `AFTER` triggers (`INSERT`, `DELETE`, `UPDATE`). Direct table edits desync search.
- **Search CLI**: `story-db --db stories/stories.db search "query" [--author X] [--category Y] [--date-from ...] [--limit 20] [--snippets]` (subcommands: `search`, `get`, `list`, `stats`).

### 4. Analysis & Vector Pipeline
Execute in order (argparse + GPU-first `--gpu` flag, idempotent skip):
1. `python -m storybuilder.analysis.extract_entities --stories-dir nifty_stories --gpu`
2. `python -m storybuilder.analysis.analyze_sentiment --stories-dir test_stories --gpu`
3. `python -m storybuilder.analysis.generate_embeddings --stories-dir test_stories` (populates dual Chroma collections: `story_chunks` + `story_averages`)
4. `python -m storybuilder.analysis.find_similar "path/to/story.txt"`
5. `python -m storybuilder.analysis.visualize_arcs --story "slug" --window 100`
6. `python -m storybuilder.analysis.compare_narratives --clusters 4`
7. `python -m storybuilder.analysis.visualize_tsne --perplexity 1000`
8. `python -m storybuilder.genai.test_voices`

### 5. TTS Prompt Crafter & Generation
- **Prompt Splitter**: `python .agent/skills/tts-prompt-crafter/scripts/split_prompts.py <dir-containing-*-scene*.md>`
  - Archives original `*-scene*.md` files into zero-padded `01-part.md`, `02-part.md`, etc. Chunks on 3rd unique speaker or >1800 characters.
  - Mandatory header: Must start with exact literal `# SYSTEM PREAMBLE: Synthesize speech ONLY for the transcripts under the #### TRANSCRIPT headers. ...` (prevents model reading structural headings aloud).
  - Schema structure: `# AUDIO PROFILE`, `### THE SCENE`, `### DIRECTOR'S NOTES` (`Style: - Name (Voice: VoiceName): desc`), `### SAMPLE CONTEXT`, `#### TRANSCRIPT`.
  - Emotion tags: Inline English only (`[whispers]`), Intimacy Palette for erotic scenes. Adjacent tags like `[sighs][whispers]` trigger API parse errors (splitter emits warning). Bracket symmetry strictly validated.
- **Gemini TTS Client**: `genai-tts --dir stories/<slug>` (or `python -m storybuilder.genai.client --dir ...`)
  - Uses `client.interactions.create()`. Skips existing `.wav`. Retries 429 quota with 15s backoff, 2s sleep between files. Uses `previous_interaction_id` for stateful voice continuity.
  - Voice constraints: Max 2 voices per call. Single-speaker prompts are padded with `{"speaker": "Dummy", "voice": "Puck"}` to avoid HTTP 400 invalid input errors. No-speaker fallback: `Kore`.
- **Cartesia TTS**: Always fetch `https://docs.cartesia.ai/llms.txt` before invoking APIs. Default header: `Cartesia-Version: 2026-03-01`.

---

## Conventions & Integration

### Code & Test Standards
- **Testing**: `uv run pytest` (runs `unittest.TestCase` modules under `tests/`). Uses `unittest.mock.patch` for network/cache isolation and `tempfile.mkdtemp()`.
- **Style Rules**: Python 3.12+ type hints required. Use `argparse` for all CLIs. Threading lock objects use `_lock` suffix (`print_lock`, `cache_lock`, `seen_folders_lock`).

### Git & Linear Integration
- **Git**: Branch off `main`. Use conventional commit prefixes (`feat:`, `fix:`).
- **Changelog**: Append summary to `./**/CHANGELOG.md` following standard format (best-effort, non-blocking).
- **Linear**: PRs automatically sync via `.github/workflows/auto-linear.yml` using `PRO` team key and `GIT-` issue prefix. `tasks/TASKS.md` tracks tasks. GraphQL API: `https://api.linear.app/graphql`.
