# StoryBuilder

StoryBuilder is an integrated Python toolkit and pipeline designed to scrape, store, analyze, embed, and synthesize audio from narrative fiction. It streamlines NLP-driven narrative analysis and provides deep multi-speaker Text-to-Speech (TTS) capabilities.

---

[![Duplicated Lines (%)](https://sonarcloud.io/api/project_badges/measure?project=jgf-dev_story-builder&metric=duplicated_lines_density&token=9085b2f9af74d4fafdc72f20b64abe67ea3d0e56)](https://sonarcloud.io/summary/new_code?id=jgf-dev_story-builder)
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=jgf-dev_story-builder&metric=bugs&token=9085b2f9af74d4fafdc72f20b64abe67ea3d0e56)](https://sonarcloud.io/summary/new_code?id=jgf-dev_story-builder)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=jgf-dev_story-builder&metric=alert_status&token=9085b2f9af74d4fafdc72f20b64abe67ea3d0e56)](https://sonarcloud.io/summary/new_code?id=jgf-dev_story-builder)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=jgf-dev_story-builder&metric=reliability_rating&token=9085b2f9af74d4fafdc72f20b64abe67ea3d0e56)](https://sonarcloud.io/summary/new_code?id=jgf-dev_story-builder)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=jgf-dev_story-builder&metric=security_rating&token=9085b2f9af74d4fafdc72f20b64abe67ea3d0e56)](https://sonarcloud.io/summary/new_code?id=jgf-dev_story-builder)
[![Technical Debt](https://sonarcloud.io/api/project_badges/measure?project=jgf-dev_story-builder&metric=sqale_index&token=9085b2f9af74d4fafdc72f20b64abe67ea3d0e56)](https://sonarcloud.io/summary/new_code?id=jgf-dev_story-builder)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=jgf-dev_story-builder&metric=sqale_rating&token=9085b2f9af74d4fafdc72f20b64abe67ea3d0e56)](https://sonarcloud.io/summary/new_code?id=jgf-dev_story-builder)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=jgf-dev_story-builder&metric=vulnerabilities&token=9085b2f9af74d4fafdc72f20b64abe67ea3d0e56)](https://sonarcloud.io/summary/new_code?id=jgf-dev_story-builder)

---

## 🚀 Key Features

* **Automated Downloader & Scraper**: Robust multi-threaded scraper for [Nifty Archive](https://nifty.org) and [Nifty Search](https://search.niftyarchives.org), including SOCKS5 proxy support, automatic IP rotation, and comprehensive SQLite metadata caching.
* **Idempotent SQLite DB Integration**: Import crawled text, automatically extract authors and structural markers, and enable ultra-fast Full-Text Search (FTS5).
* **NLP & Sentiment Analysis**: Extract named entities (people, places, organizations) and sentence-level sentiment curves using GPU-accelerated spaCy models and HuggingFace transformers.
* **Vector Embeddings & Semantic Search**: Generate sentence-transformer embeddings, persist them in ChromaDB collections, and retrieve semantically similar stories.
* **Interactive Narrative Visualizations**: Generate Plotly-based HTML plots of characters' emotional trajectories (emotional arcs) and t-SNE clustering visualizations.
* **Streamlit Dashboard**: Search, read, favorite/tag, and inspect archive stats over the SQLite store.
* **Multi-Speaker TTS Generation**: Intelligently chunk narrative transcripts by scenes and character dialogue, auto-assign voices (Gemini TTS / Cartesia), and output high-quality multi-speaker audio.
* **ADK Agents**: `tts_prompt_crafter` (and a Cartesia YAML sibling) turn raw stories into canonical TTS prompt files. See [evals/README.md](evals/README.md).

---

## 🛠️ Tech Stack

* **Runtime**: Python 3.12 (managed with `uv`)
* **NLP**: spaCy, HuggingFace transformers
* **Database**: SQLite (FTS5 + Triggers), ChromaDB vector store
* **Embeddings**: sentence-transformers
* **TTS**: Google GenAI, Cartesia
* **UI**: Streamlit
* **Agents**: Google ADK
* **Visualization**: Plotly, Scikit-learn (K-Means, t-SNE), Matplotlib

Console scripts from `pyproject.toml`: `downloader`, `genai-tts`. There is no `storybuilder` CLI entrypoint.

---

## 📂 Codebase Directory Structure

```text
story-builder/
├── pyproject.toml               # Package configuration and dependencies
├── src/storybuilder/
│   ├── downloader/              # Scraping, IP rotation, writer, SQLite, S3/GCS upload
│   ├── analysis/                # Sentiment, entity, embedding, and visualization CLIs
│   ├── genai/                   # Gemini TTS, Cartesia client, voice helpers
│   ├── dashboard/               # Streamlit pages (search, read, favorites, stats)
│   ├── agents/                  # ADK tts_prompt_crafter + cartesia_tts_prompt_crafter
│   └── utils/                   # Env/key rotation, HuggingFace upload helpers
├── scripts/
│   ├── import_to_sqlite.py      # Idempotent DB importer with FTS5 table setup
│   ├── story_db.py              # FTS search, retrieval, and stats CLI
│   ├── dashboard.py             # Streamlit entry
│   ├── migrate_email_date.py    # Drop legacy email_date
│   └── repartition_db.py        # Year-partition helper (legacy layout)
├── evals/                       # ADK / agentic evaluation
└── tests/                       # Unit and integration test suite
```

---

## ⚙️ Setup & Installation

### 1. Synchronize Dependencies

```bash
uv sync --all-extras --dev
```

### 2. Download spaCy NLP Models

```bash
uv run python -m spacy download en_core_web_sm
uv run python -m spacy download en_core_web_lg
```

Entity extraction defaults to `en_core_web_lg`. Evals only require `en_core_web_sm`.

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY="your-gemini-key"
# Quota rotation support:
GEMINI_API_KEY_1="your-backup-key-1"
GEMINI_API_KEY_2="your-backup-key-2"

CARTESIA_API_KEY="your-cartesia-key"
```

Optional:

```env
STORYBUILDER_DB_DIR=stories/db
STORYBUILDER_NLP_DB_PATH=stories/db/nlp_analysis.db
STORYBUILDER_META_DB_PATH=stories/db/dashboard_metadata.db
DASHBOARD_DEV_MODE=true
STORIES_TEXT=/absolute/path/to/stories
HF_TOKEN=...
STORYBUILDER_LIVE_API=1
```

---

## 🔄 End-to-End Execution Pipeline

### Step 1: Scrape & Download Stories

The console script is **`downloader`** (also `python -m storybuilder.downloader.cli`). Default output is `stories/text`; default SOCKS5 proxy is `192.168.2.10:37459`.

```bash
downloader --category gay --start-date 1990-01-01 --end-date 2025-12-31 --output-dir stories/text --socks5-proxy 127.0.0.1:1080 --rotate-on-refusal --max-workers 5 --max-scraping 5
```

Useful flags: `--force` (bypass cache early-stop), `--delay` (parser default `0.01`; help text still says `1.0`), `--db stories/db`, `--s3-bucket` / `--gcs-bucket`.

SOCKS5 needs `pysocks`. HTTP 403/429/503 can trigger Windscribe IP rotation when `--rotate-on-refusal` is set.

### Step 2: Index Content into SQLite

```bash
python3 scripts/import_to_sqlite.py --db stories/stories.db
```

If you already have an older database that still contains the removed
`email_date` column, it will be migrated automatically the next time the DB is
opened through the shared SQLite layer. You can also migrate it manually with:

```bash
python3 scripts/migrate_email_date.py stories/stories.db
```

FTS5 stays in sync **only** via AFTER INSERT/DELETE/UPDATE triggers. Direct table edits desync search.

### Step 3: Run NLP Analysis

```bash
python3 -m storybuilder.analysis.analyze_sentiment --stories-dir stories/text --gpu
python3 -m storybuilder.analysis.extract_entities --stories-dir stories/text --gpu
```

### Step 4: Embed & Search

```bash
python3 -m storybuilder.analysis.generate_embeddings --stories-dir stories/text
python3 -m storybuilder.analysis.find_similar "stories/text/gay/subcat/slug/story.txt"
```

### Step 5: Visualize

```bash
python3 -m storybuilder.analysis.visualize_arcs --story "story-slug" --window 100
python3 -m storybuilder.analysis.visualize_tsne --perplexity 1000
```

### Step 6: Browse the dashboard

```bash
streamlit run scripts/dashboard.py
```

Pages: Search & Explorer, Read Story, Favorites & Tags, Archive Stats. Defaults: `STORYBUILDER_DB_DIR=stories/db`. Set `DASHBOARD_DEV_MODE=true` to reload dashboard modules on each run.

### Step 7: Generate TTS Audio

Gemini (skips existing `.wav`; stateful interaction continuity across parts):

```bash
genai-tts --dir stories/the_secret_vacation
# or
python3 -m storybuilder.genai.client --dir stories/the_secret_vacation
```

Cartesia (`*-part.md` → `.wav`, default 24 kHz):

```bash
python3 -m storybuilder.genai.cartesia_client --dir stories/the_secret_vacation --rate 24000
```

`--dir` must exist. Sample trees live under `stories/text/`, not `stories/the_secret_vacation`, unless you create that folder.

---

## 🤖 ADK agents

`tts_prompt_crafter` (`src/storybuilder/agents/tts_prompt_crafter/`) is a three-agent pipeline: story analyzer → scene writer → root orchestrator. Tools: `read_story`, `list_stories`, `write_scene_file`, `split_scene_files`. Story files are resolved under `stories/text` unless you pass an absolute path.

Constraints (Gemini): max 2 voices per call; single-speaker prompts are padded with a Dummy/Puck speaker; adjacent emotion tags like `[sighs][whispers]` fail API parse.

Split scene files:

```bash
python .agent/skills/tts-prompt-crafter/scripts/split_prompts.py <dir-containing-*-scene*.md>
```

A YAML Cartesia sibling lives at `src/storybuilder/agents/cartesia_tts_prompt_crafter/` and is not exported from `agents/__init__.py`.

Eval how-to: [evals/README.md](evals/README.md).

Gotchas:

* Vertex memory bank IDs are hardcoded in `agent.py` (`storage-499607` / engine `8434441657599918080`).
* OTEL exporters target `http://localhost:4318`.
* Sessions persist to `stories/db/tts_prompt_crafter.db`.

---

## 🧪 Running Tests

CI and local development use `uv run pytest` (unittest-style cases under `tests/`). Network and heavy model downloads are mocked.

```bash
uv run pytest
uv run pytest tests/downloader tests/dashboard -q
uv run pytest evals/ -v -m "not slow"
```

Markers: `slow`, `adk_eval`, `agentic`, `integration`. Live Gemini/Vertex/TTS paths stay off unless `STORYBUILDER_LIVE_API=1`.

---

## 🧯 Troubleshooting

| Symptom | Fix |
| ------- | --- |
| `storybuilder: command not found` | Use `downloader` or `python -m storybuilder.downloader.cli`. |
| SOCKS import error | `uv sync` (pulls `pysocks`) or install `pysocks`. |
| Downloader 403/429 | Enable `--rotate-on-refusal`; confirm the SOCKS5 proxy is up. |
| FTS search empty after SQL edits | Re-import or avoid writing `stories` without the triggers. |
| `CARTESIA_API_KEY not found` | Load `.env`; Cartesia client reads it via `load_env()`. |
| Cartesia/Gemini `--dir` missing | The default `stories/the_secret_vacation` is not shipped; pass a real directory of `*-part.md` files. |
| Dashboard empty | Point `STORYBUILDER_DB_DIR` at the SQLite directory used by import/downloader (`stories/db` by default). |
