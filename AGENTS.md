# AGENTS.md

This file captures non-obvious knowledge required to work effectively in this repository. It is derived strictly from observed files, configs, code, tests, CI, and existing rule docs. Only what was directly read is documented.

## Project Overview

StoryBuilder is a Python toolkit for analyzing, embedding, and generating audio from narrative fiction. The main workflow observed in this repo is:

1. Scrape and archive stories.
2. Import story text into SQLite and FTS5.
3. Extract entities, sentiment, and embeddings.
4. Generate and validate TTS prompts and audio.

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12+ |
| Package manager | uv |
| NLP | spaCy, HuggingFace transformers |
| Embeddings | sentence-transformers, ChromaDB |
| Visualization | Plotly, matplotlib, scikit-learn |
| TTS | Google GenAI |
| Cloud | AWS Bedrock AgentCore, Boto3 |
| Data | SQLite |

## Directory Structure

- `src/storybuilder/` - importable package for downloader, genai, cartesia, xaiapi, bedrock, and utils
- `scripts/` - SQLite import/query tooling
- `tests/` - unittest coverage for downloader, TTS, and prompt splitting
- `.agent/skills/` - agent-facing workflow docs and scripts
- `stories/` and `nifty_stories/` - story text and archived audio parts
- `src/prompts/` - example prompt templates

## Essential Commands

**Environment setup (required before most work):**

- `uv sync --all-extras --dev` (from `.github/workflows/test.yml:30` and QWEN.md)
- `python -m spacy download en_core_web_sm && python -m spacy download en_core_web_lg` (QWEN.md prerequisites; required for analyze_sentiment.py and extract_entities.py)
- Create `.env` with `GEMINI_API_KEY` (and optionally `GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, ... for quota rotation), `CARTESIA_API_KEY`, `XAI_API_KEY` (and management key), and any AWS creds needed for boto.py.
- There are more than one GEMINI API KEY in `.env`. If you hit a quota limit, try a different one, named GEMINI_API_KEY_1, GEMINI_API_KEY_2, GEMINI_API_KEY_3, etc.

**Testing:**

- `uv run pytest` (CI step at `.github/workflows/test.yml:33`; runs unittest-based tests under `tests/`)

**Python rules:**

- Always add type hints. Resolve mismatch warnings.
- Avoid overly lengthy functions or files. Seperate logic accordingly.

**Downloader (Nifty Archive scraper + parallel fetcher):**

- Via installed entrypoint: `storybuilder --category gay --start-date 1990-01-01 --end-date 2025-12-31 --output-dir nifty_stories --socks5-proxy 192.168.2.10:37459 --rotate-on-refusal --max-scraping 5 --max-workers 5`
- Or direct: `python -m storybuilder.downloader.cli ...` (same flags)
- `--force` disables cache-based early-stop (cli.py:28, scraper.py:143)
- `--delay` controls inter-request sleep (default 0.01s in parser, 1.0 described in help text)
- Requires `pysocks` (hard runtime check in cli.py:40-47); sets `network.PROXIES` and `network.ENABLE_ROTATION`

**TTS prompt splitting (Gemini 2-voice + length compliance):**

- `python .agent/skills/tts-prompt-crafter/scripts/split_prompts.py <dir-containing-*-scene*.md>`
- Example from SKILL.md: `python .agent/skills/tts-prompt-crafter/scripts/split_prompts.py .agent/skills/google-genai-sdk/example`
- Input files must be archived by the script; outputs are `01-part.md`, `02-part.md`, ...

**TTS generation (Gemini interactions API):**

- `python src/storybuilder/genai/client.py --dir stories/the_secret_vacation` (or any dir with `*-part.md` files)
- Skips existing `.wav`; uses stateful `previous_interaction_id`; 15s backoff on 429/quota; 2s inter-file sleep

**DB import and query (stories.db with FTS5):**

- `python scripts/import_to_sqlite.py [--db stories/stories.db] [--limit N] [--force]` (idempotent on UNIQUE path; builds FTS5 + triggers)
- `python scripts/story_db.py --db stories/stories.db search "query" [--author X] [--category Y] [--date-from ...] [--limit 20] [--snippets]`
- Subcommands observed: `search`, `get` (by path/slug; supports --export), `list`, `stats`

**Analysis / embedding / viz scripts (root level, from QWEN.md and file headers):**

- `python -m storybuilder.analysis.analyze_sentiment --stories-dir test_stories --gpu`
- `python -m storybuilder.analysis.generate_embeddings --stories-dir test_stories`
- `python -m storybuilder.analysis.find_similar "path/to/story.txt"`
- `python -m storybuilder.analysis.visualize_arcs --story "slug" --window 100`
- `python -m storybuilder.analysis.compare_narratives --clusters 4`
- `python -m storybuilder.analysis.visualize_tsne --perplexity 1000`
- `python -m storybuilder.analysis.extract_entities --stories-dir nifty_stories --gpu`
- `python -m storybuilder.genai.test_voices` (Gemini multi-speaker TTS test)

**Cartesia (per SKILL.md):**

- Always fetch `https://docs.cartesia.ai/llms.txt` first before using any API details.
- Typical: `uv sync && CARTESIA_API_KEY=... uv run python ...` (examples live in `src/storybuilder/cartesia/calls.py`)

## Running Pipeline

Typical observed order for analysis work:

1. `python -m storybuilder.analysis.extract_entities --stories-dir nifty_stories --gpu`
2. `python -m storybuilder.analysis.analyze_sentiment --stories-dir test_stories --gpu`
3. `python -m storybuilder.analysis.generate_embeddings --stories-dir test_stories`
4. `python -m storybuilder.analysis.find_similar "path/to/story.txt"`
5. `python -m storybuilder.analysis.visualize_arcs --story "slug" --window 100`
6. `python -m storybuilder.analysis.compare_narratives --clusters 4`
7. `python -m storybuilder.analysis.visualize_tsne --perplexity 1000`
8. `python -m storybuilder.genai.test_voices`

## Git Conventions

- Branching is observed on `main`.
- Recent commits use conventional commit prefixes like `feat:` and `fix:`.

## Code Organization and Structure

**High-level layout (observed via ls + QWEN.md + imports):**

- `src/storybuilder/` — importable package (downloader, genai, cartesia, xaiapi, bedrock, utils)
- Root Python scripts — standalone analysis/entry tools (analyze_sentiment.py, generate_embeddings.py, visualize_*.py, import_to_sqlite.py, story_db.py, test_voices.py, boto.py, etc.)
- `.agent/skills/` — agent-facing workflows (tts-prompt-crafter with SKILL.md + splitter script; google-genai-sdk with resources)
- `src/prompts/` — example prompt templates (gemini_tts.md, tommy.json)
- `tests/` — unittest modules mirroring key logic
- `stories/` (and `nifty_stories/` output) — story text + archived audio parts
- `scripts/` — DB tooling
- `.github/workflows/test.yml`, `pyproject.toml`, `.python-version` — build/CI

**Key subsystems and control/data flow (from full file reads):**

**Downloader (two-phase: scrape targets then download):**

- `cli.py` (argparse, ThreadPoolExecutor for max-scraping subcats + max-workers downloads, cache load/save wrapper, proxy/rotation setup, date parsing)
- `scraper.py`: `get_subcategories` (BeautifulSoup list-group-item + fallback links), `parse_listing_rows` (handles both `div.ftr` and `tr/td` formats), `scrape_subcategory` (pagination via `.jscroll-next`, cache lookup + `is_cache_sufficient`, per-row `parse_nifty_date`, early-stop on date or cache hit), `scrape_multi_chapter_folder` (folder_date cache), `process_subcategory` (seen_folders thread lock, output path construction for cat/sub/slug)
- `network.py`: global `PROXIES`/`ENABLE_ROTATION`, `rotate_windscribe_ip` (subprocess), `fetch_page` (retries, 404→None, rotation trigger on 403/429/503 + ConnectionError/Timeout)
- `cache.py`: `print_lock`/`cache_lock`, `metadata_cache` dict, `load_cache`/`save_cache` (per-output-dir `metadata_cache.json` with "stories", "complete", "folder_date")
- `date_parser.py`: `parse_nifty_date` (MMM DD YYYY, MMM DD HH:MM with ref-year imputation + future→prev-year roll, fallback "Jun 6")
- `writer.py`: `save_story` (HTML→BeautifulSoup p extraction or email header parse; prepends ===== Title/Author/Date/URL header), `download_single_target` (primary download + shutil.copy2 for duplicates across subcats)

**TTS prompt lifecycle:**

- Human/LLM annotation produces `*-scene*.md` files following strict schema (see below).
- `split_prompts.py:process_files` (glob `*-scene*.md`, archive originals, chunk on 3rd unique speaker or >1800 chars, `filter_preamble_speakers`, bracket-symmetry validation, adjacent-tag warning, emit `NN-part.md`)
- `genai/client.py:process_directory` (glob `*-part.md`, skip existing wav, `parse_speech_config`, `client.interactions.create(..., previous_interaction_id=..., generation_config={"speech_config": [...]})`, rate-limit retry, 2s sleep)

**DB layer:**

- `import_to_sqlite.py`: exact `=====` header parsing (two markers), `parse_author` (Name <email>), chapter suffix regex, FTS5 virtual table with external content + 3 AFTER INSERT/DELETE/UPDATE triggers for sync, UNIQUE(path) idempotency, indexes
- `story_db.py`: argparse subparsers, `connect` (row_factory), `cmd_search` (FTS MATCH + WHERE filters + snippet), `cmd_get` (path/slug lookup + optional export), `cmd_list`/`cmd_stats`

**Other observed patterns:**

- GPU selection in root scripts (spacy, sentence-transformers device, thinc)
- Dual Chroma collections (story_chunks + story_averages) per QWEN.md
- src-layout sys.path hacks in `src/storybuilder/main.py` and `src/storybuilder/downloader/cli.py` for direct execution
- Thread-safe printing via locks in downloader

## Naming Conventions and Style Patterns

- All CLIs use `argparse` (no click/typer observed).
- Modules: snake_case (date_parser.py, split_prompts.py).
- Threading primitives: explicit `_lock` suffix (`print_lock`, `cache_lock`, `seen_folders_lock`).
- Cache metadata: `metadata_cache.json` containing per-URL dicts with "stories", "complete", "last_updated", "folder_date".
- TTS prompt files: `NN-sceneX.md` → splitter produces `NN-part.md` (zero-padded).
- Story output layout: `nifty_stories/<category>/<subcategory>/<slug>/...-N.txt` (or flat for single-chapter).
- Prompt schema (mandatory, observed in SKILL.md + gemini_tts.md + tests):
  - Starts with literal `# SYSTEM PREAMBLE: Synthesize speech ONLY for the transcripts under the #### TRANSCRIPT headers. ...`
  - Sections: `# AUDIO PROFILE`, `### THE SCENE`, `### DIRECTOR'S NOTES` (with `Style:` bullets of form `- Name (Voice: VoiceName): desc`), `### SAMPLE CONTEXT`, `#### TRANSCRIPT`
  - Transcript lines: `CharacterName: dialogue...` or `Narrator: ...`; emotion tags `[word]` inline; one-breath-per-line preferred.
- Emotion tags: English only; never adjacent `][` without separator; Intimacy Palette for erotic scenes (whispers/sighs/gasp etc.); no shouting/excited in intimacy.
- Tests: `TestClassName` inheriting `unittest.TestCase`; methods `test_...`; heavy use of `@patch`, `tempfile`, `shutil`.
- Imports inside tests often use full `from storybuilder....` after path hacks.

## Testing Approach and Patterns

- Framework: `unittest` (not pytest-style classes/functions); run via `uv run pytest` (which discovers them).
- CI: fresh checkout → `uv sync --all-extras --dev` → `uv run pytest` (test.yml:29-33).
- Mocks: `unittest.mock.patch` on `requests.get`, `rotate_windscribe_ip`, `fetch_page`, `save_story`.
- FS isolation: `tempfile.mkdtemp()`, explicit cleanup in tearDown/finally.
- Verified behaviors exercised in tests (and thus must be preserved):
  - Date parsing with/without year + future-year roll under reference_date.
  - Dual `parse_listing_rows` formats (ftr divs + tr/td).
  - Cache load/save roundtrip.
  - Network: 200 success, 404→None, 403/429/503 + exceptions trigger rotation when ENABLE_ROTATION.
  - Writer: HTML title/author extraction, text email headers, duplicate-target copy.
  - `parse_speech_config`: multi-speaker, single→Dummy/Puck padding, no-speakers→Kore fallback, max-2 truncation.
  - Splitter: bracket-aware sentence split, preamble speaker filtering, 3rd-speaker + 1800-char chunking, archive move, adjacent-tag WARNING emitted but processing continues, bracket-symmetry raise on mismatch.

## Important Gotchas or Non-Obvious Patterns

**Downloader / Nifty specifics:**

- Cache early-stop is safe **only if** `is_complete` (reached_end) **or** `min_cached_date <= start_date` (scraper.py:142). `force` bypasses. Without this, historical pages are re-crawled.
- Multi-chapter "Dir" entries use separate `folder_date` cache key; if no chapter in range, the whole folder is skipped (scraper.py:288-293).
- Date strings from `ls`-style listings have no year for recent files; `parse_nifty_date` imputes from reference (today or passed) and rolls future dates to prior year (date_parser.py:39-41, 55-56). Fallback regex for bare "Jun 6".
- Duplicate stories across subcategories are handled by collecting multiple output_paths per key and using `shutil.copy2` after first download (writer.py:99-108) — avoids re-fetch.
- SOCKS5 proxy setup is **not** optional once flag is given: hard ImportError + instructions if pysocks missing (cli.py:40-47). Rotation only happens on specific HTTP statuses or network exceptions (network.py:55-64).
- `seen_folders` lock prevents concurrent re-processing of the same multi-chapter folder across subcategory workers.

**TTS / prompt specifics (critical for API success):**

- Every `*-scene*.md` / `*-part.md` **must** start with the exact `# SYSTEM PREAMBLE...` line (SKILL.md line 28, gemini_tts.md). Without it the model reads headings aloud → PROHIBITED_CONTENT or garbage.
- Google GenAI TTS enforces ≤2 voices per call. `parse_speech_config` (genai/client.py:21-45) truncates to 2; for single-speaker it **pads** `{"speaker":"Dummy","voice":"Puck"}` specifically to avoid 400 Invalid Input on chunks that happen to have only one speaker.
- Adjacent tags like `[sighs][whispers]` cause TTS API parse error. Splitter prints WARNING (split_prompts.py:83-86) but still emits the line; human must fix. Bracket symmetry is strictly validated (raises ValueError).
- Splitter also enforces ~1800 char chunks in addition to speaker limit (split_prompts.py:117).
- Stateful continuity uses `previous_interaction_id` (genai/client.py:87); still, every chunk's Style section must repeat the voice assignments for stability.
- Cartesia work: **never** guess endpoints/voices/params — fetch <https://docs.cartesia.ai/llms.txt> first (SKILL.md rule 1). Default Cartesia-Version header is 2026-03-01.

**DB / import:**

- stories.db import expects the exact two-line `=====` header + Title/Author/Publication Date/URL fields produced by the downloader writer. Email-style headers are parsed differently.
- FTS5 is external-content and kept in sync **exclusively** by the three AFTER triggers in import_to_sqlite.py:54-69. Direct table edits will desync search.
- Idempotency is on `path` (UNIQUE); `--force` in import script overrides.

**Environment / runtime:**

- Many heavy optional deps (spacy[cuda12x], sentence-transformers, chromadb, cartesia, transformers, xai-sdk, etc.). Outside a full `uv sync --all-extras` + model downloads, static analysis and direct `python` runs will show dozens of "could not be resolved" errors — this is expected.
- `.gitignore` hides `.env`, `uv.lock`, `*.db`, `test_stories/`, `chroma_db/`, `dist/`.
- Multiple GEMINI keys: rotate via `GEMINI_API_KEY_1` etc. when quota hit (observed in `.agent/AGENTS.md` and genai retry logic).
- sys.path manipulation appears in package mains because of src-layout + desire to run files directly.

**Rule file context (must be respected):**

- `.agent/AGENTS.md`: "There are more than one GEMINI API KEY in `.env`. If you hit a quota limit, try a different one, named GEMINI_API_KEY_1, GEMINI_API_KEY_2, GEMINI_API_KEY_3, etc."
- `QWEN.md`: authoritative observed overview (tech stack, design patterns like SQLite idempotency + dual Chroma + GPU-first + argparse everywhere, git notes, pipeline order).
- `.agent/skills/tts-prompt-crafter/SKILL.md`: mandatory preamble, exact scene prompt schema, emotion tag rules (Intimacy Palette, no adjacent, English only), "one breath per line", acoustic principles (proximity effect, glottal flow, ASMR pacing), M4M voice matrix, anti-patterns.
- `src/storybuilder/cartesia/SKILL.md`: fetch llms.txt first, Cartesia-Version, auth model, generation_config, SSML, non-invention rule.
- `src/prompts/gemini_tts.md`: concrete example of required AUDIO PROFILE + DIRECTOR'S NOTES + THE SCENE + TRANSCRIPT structure.

## Additional Project-Specific Notes

- Branching: observed `main`; recent commits use conventional style.
- Story content is large; parts of `stories/` and `nifty_stories/` may be gitignored or stored as archives (e.g., .7z + wav backups).
- The downloader is tightly coupled to current Nifty HTML structure (two listing formats already handled; fragile to site changes).
- All root analysis scripts follow the "argparse + GPU flag + idempotent skip if already processed" pattern per QWEN.

When adding features or fixing bugs, cross-check the exact behaviors exercised in `tests/test_downloader.py`, `tests/test_genai.py`, and `tests/test_split_prompts.py` — they encode the contract for cache logic, date parsing, dummy padding, chunking, and warning semantics.
<<<<<<< HEAD
<<<<<<< HEAD

## Linear Integration

- **Workflow**: `.github/workflows/auto-linear.yml` runs on every PR, finds-or-creates a Linear issue (team key `PRO`, title prefix `GIT-`), and prefixes the PR title. Uses `ctriolo/action-find-or-create-linear-issue@v0.60`.
- **Task tracking**: The canonical task list is [`tasks/TASKS.md`](tasks/TASKS.md). Unchecked `- [ ]` items under "Active" are candidates for Linear issue creation.
- **Secret**: `LINEAR_API_KEY` is stored in GitHub Secrets (not in `.env`). For local Linear API calls, the user must export it.
- **Prompt**: Use `/linear-assistant` (`.github/prompts/linear-assistant.prompt.md`) to create, find, or sync Linear issues from chat.
- **Convention**: All Linear issue titles are prefixed with `GIT-` to match the auto-linear workflow. Use the `PRO` team key.
- **API**: Linear GraphQL endpoint is `https://api.linear.app/graphql`. Prefer GraphQL over REST.
=======
>>>>>>> palette/save-button-tooltip-16022957350325416287
