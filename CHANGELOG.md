# Changelog

All notable changes to this project will be documented in this file.
<<<<<<< HEAD

## [HASH](https://github.com/jgf2/story-builder/commit/HASH) - 2026-08-05
=======
## [HASH](https://github.com/jgf2/story-builder/commit/HASH) - 2026-08-15

### Summary
Resolved the pull request merge conflicts against `origin/main`.

### Fixed
- Merged the latest `origin/main` changes into this branch and resolved the remaining conflict markers across the affected source, test, and changelog files.
- Preserved the integer `--limit` default in `src/storybuilder/analysis/generate_embeddings.py` while keeping the current `main` signatures and tests.

## [HASH](https://github.com/jgf2/story-builder/commit/HASH) - 2026-08-10

### Summary
Resolved merge conflicts between this pull request branch and `origin/main` across dashboard, downloader, GenAI, and test files.

### Fixed
- Merged the latest `origin/main` changes into the branch and removed the remaining conflict markers from the affected source and test files.
- Preserved the branch changelog history while restoring the newer `dashboard.html` changelog entry from `main`.

## [f2fbd13](https://github.com/jgf2/story-builder/commit/f2fbd132e346eef5e6bc840d8bb3cbb4065def0c) - 2026-08-04

### Summary
Resolved merge conflicts across 24 files including analysis scripts, downloader modules, utils, dashboard, and test suites. Preserved tab indentation and verified test suite (86 passed).

### Fixed
- Fixed nested merge conflict markers in `.agent/skills/cartesia_tts_api/scripts/calls.py`, `src/storybuilder/utils/env.py`, `src/storybuilder/utils/logging_config.py`, `src/storybuilder/utils/storage.py`, and `src/storybuilder/genai/fix_prompts2.py`.
- Preserved `_process_subcategory_page` scraper helper in `src/storybuilder/downloader/scraper.py`.
- Standardized tab indentation in `tests/dashboard/test_dashboard.py` and `tests/genai/test_cartesia.py`.
## [cc73bb8](https://github.com/jgf2/story-builder/commit/cc73bb8e54a3ea16685b49cb3f188378de2473ea) - 2026-08-04

### Summary
Resolved merge conflict in `scripts/import_to_sqlite.py`. Preserved typed `_flush_batch` signature with tab indentation and verified test suite (`tests/downloader/test_database.py`).

### Fixed
- Standardized tab indentation for `_flush_batch` in `scripts/import_to_sqlite.py`.
## [34ad68f](https://github.com/jgf2/story-builder/commit/34ad68fef72a5043f0d324571df13c002df2662e) - 2026-08-04

### Summary
Resolved merge conflicts across database import scripts, analysis routines, dashboard data structures, downloader modules, and test suites. Standardized tab indentation and verified test suite (86 passed).

### Fixed
- Fixed nested merge conflicts in `.agent/skills/cartesia_tts_api/scripts/calls.py` and `.agent/resolve_conflicts.py`.
- Preserved `_meta_db_initialized_paths` state in `src/storybuilder/dashboard/data.py`.
- Fixed tab vs space indentation in `tests/analysis/test_analyze_sentiment.py` and `tests/dashboard/test_dashboard.py`.
## [93391a5](https://github.com/jgf2/story-builder/commit/93391a56a5624dcad98656cd2033d526eb2bf77b) - 2026-08-04

### Summary
Resolved merge conflict in `tests/genai/test_play_audio.py`. Retained both `get_audio_player` and `natural_sort_key` unit test suites with tab indentation, and verified tests (9 passed).

### Fixed
- Combined unit test suites for `get_audio_player` and `natural_sort_key` in `tests/genai/test_play_audio.py`.
## [7c4211b](https://github.com/jgf2/story-builder/commit/7c4211b4105f93589eab59706c7453d1989357b0) - 2026-08-04

### Summary
Resolved merge conflict in `src/storybuilder/analysis/analyze_sentiment.py`. Standardized tab indentation for `process_chapter` and verified test suite (`tests/analysis/test_analyze_sentiment.py`).

### Fixed
- Preserved tab indentation and fallback text truncation logic in `src/storybuilder/analysis/analyze_sentiment.py`.
## [a9efce2](https://github.com/jgf2/story-builder/commit/a9efce27f95eab61423434314a58c9c787097218) - 2026-08-04

### Summary
Merged `origin/main` into `tests/play-audio-1319523169601476082`. Resolved merge conflicts in `.mergify.yml`, `CHANGELOG.md`, `scripts/import_to_sqlite.py`, and `src/storybuilder/dashboard/config.py`. Fixed test class structure in `tests/dashboard/test_dashboard.py` and verified test suite (90 passed).

### Fixed
- Resolved merge conflict in `.mergify.yml` by keeping `jules` and `failures` label actions.
- Preserved dynamic `sys.modules` fallback in `src/storybuilder/dashboard/config.py`.
- Formatted `_flush_batch` type hints in `scripts/import_to_sqlite.py`.
- Fixed `TestDashboardConfig` class indentation in `tests/dashboard/test_dashboard.py`.
## [PR-1689](https://github.com/jgf-dev/story-builder/pull/1689) - 2026-08-04

### Summary
Added unit tests for the `StorySearchQuery` dataclass in `storybuilder.dashboard.data`.

### Added
- `tests/dashboard/test_story_search_query.py` with tests for default and custom initialization of `StorySearchQuery`.

## [PR-XXX](https://github.com/jgf-dev/story-builder/pull/XXX) - 2026-08-04

### Summary
Deduplicated Quick Stats list styling in dashboard.html by reusing the `.notes` utility class and removing redundant `.stats` CSS.

### Fixed
- Added `.notes` utility class to `<ul class="stats">` in `dashboard.html` to share list-reset styles.
- Removed duplicate `margin`, `list-style`, `display: grid`, `gap`, and `padding` declarations from `.stats` CSS rule since they are now inherited from `.notes`.

## [0b68f42](https://github.com/jgf2/story-builder/commit/0b68f42b6bde9a6b15161a5ee1c65efebd320875) - 2026-08-04

### Summary
Resolved final git merge conflict in `tests/utils/test_logging_config.py`, verified test suite, formatted code with ruff, and completed merge onto `tests/play-audio-1319523169601476082`.

### Fixed
- Resolved tab vs space indentation conflict in `tests/utils/test_logging_config.py` and added explicit return type annotations.

## [0b8a04c](https://github.com/jgf2/story-builder/commit/0b8a04c0c25bb8f5a8b088ea54ed8764f5f4c2b2) - 2026-08-03

### Summary
Completed merge of `origin/tests/get-logger-8784844133665420913` into `tests/play-audio-1319523169601476082`. Resolved all remaining conflict markers across utilities, downloader, analysis, dashboard, and test suites, verified test suite (77 passed), and formatted code with ruff.

### Fixed
- Resolved merge conflicts in `src/storybuilder/utils/env.py`, `src/storybuilder/utils/logging_config.py`, `src/storybuilder/utils/storage.py`, and `tests/utils/test_logging_config.py`.
- Corrected variable reference `_meta_db_initialized_paths` in `src/storybuilder/dashboard/data.py`.
- Formatted all resolved Python files with `ruff`.

## [HASH](https://github.com/jgf2/story-builder/commit/HASH) - 2026-08-03

### Summary
Resolved merge conflicts across database import tools, sentiment analysis pipeline, dashboard data layer, downloader scraper, and unit test suites.

### Fixed
- Resolved merge conflict in `scripts/import_to_sqlite.py` by restoring `_flush_batch`.
- Preserved fallback handling for long texts in `src/storybuilder/analysis/analyze_sentiment.py`.
- Kept `_meta_db_initialized_paths` state tracking in `src/storybuilder/dashboard/data.py`.
- Cleaned up tab indentation and navigation state updates in `src/storybuilder/dashboard/pages/search_explorer.py`.
- Adopted refactored `_process_subcategory_page` loop in `src/storybuilder/downloader/scraper.py`.
- Consolidated unit tests in `tests/analysis/test_analyze_sentiment.py`, `tests/dashboard/test_dashboard.py`, `tests/genai/test_cartesia.py`, and `tests/genai/test_play_audio.py`.

## [HASH](https://github.com/jgf2/story-builder/commit/HASH) - 2026-08-03

### Summary
Resolved merge conflicts across dashboard reader/explorer pages, downloader package exports, and sentiment analysis test suite.

### Fixed
- Resolved merge conflicts in `src/storybuilder/dashboard/pages/read_story.py` and `search_explorer.py` by preserving `word_count` rendering.
- Retained `upload_sqlite_to_bigquery` export in `src/storybuilder/downloader/__init__.py`.
- Restored `find_multi_chapter_stories` test import in `tests/analysis/test_analyze_sentiment.py`.
## [PR-XXX](https://github.com/jgf-dev/story-builder/pull/XXX) - 2026-08-03
>>>>>>> origin/main

### Summary
Resolved git merge conflicts across 7 files (`.jules/palette.md`, `CHANGELOG.md`, `scripts/import_to_sqlite.py`, `read_story.py`, `search_explorer.py`, `storage.py`, and `test_dashboard.py`).

### Fixed
- Merged `.jules/palette.md` accessibility learnings chronologically.
- Restored typed `_flush_batch` definition in `scripts/import_to_sqlite.py`.
- Standardized tab indentation and safe `word_count` rendering in `read_story.py` and `search_explorer.py`.
- Maintained `# pyrefly: ignore [missing-import]` comment for `boto3` in `storage.py`.
- Adopted environment variable patching for test database paths in `tests/dashboard/test_dashboard.py`.


## [8d5c3f6](https://github.com/jgf2/story-builder/commit/8d5c3f68a51c87de4167a2c7ab50d1ef0cf76211) - 2026-08-04

### Summary
Resolved merge conflicts in `scripts/import_to_sqlite.py`, `src/storybuilder/dashboard/data.py`, `src/storybuilder/dashboard/pages/search_explorer.py`, and `tests/dashboard/test_dashboard.py`. Standardized tab indentation and verified test suite (76 passed).

### Fixed
- Preserved type annotations for `_flush_batch` in `scripts/import_to_sqlite.py`.
- Resolved tab vs space indentation in `src/storybuilder/dashboard/data.py`, `search_explorer.py`, and `tests/dashboard/test_dashboard.py`.
- Fixed top-level class definition for `TestDashboardConfig` in `tests/dashboard/test_dashboard.py`.

## [HASH](https://github.com/jgf2/story-builder/commit/HASH) - 2026-08-03

### Summary
Resolved merge conflicts across database import tools, sentiment analysis pipeline, dashboard data layer, downloader scraper, and unit test suites.

### Fixed
- Resolved merge conflict in `scripts/import_to_sqlite.py` by restoring `_flush_batch`.
- Preserved fallback handling for long texts in `src/storybuilder/analysis/analyze_sentiment.py`.
- Kept `_meta_db_initialized_paths` state tracking in `src/storybuilder/dashboard/data.py`.
- Cleaned up tab indentation and navigation state updates in `src/storybuilder/dashboard/pages/search_explorer.py`.
- Adopted refactored `_process_subcategory_page` loop in `src/storybuilder/downloader/scraper.py`.
- Consolidated unit tests in `tests/analysis/test_analyze_sentiment.py`, `tests/dashboard/test_dashboard.py`, `tests/genai/test_cartesia.py`, and `tests/genai/test_play_audio.py`.

## [HASH](https://github.com/jgf2/story-builder/commit/HASH) - 2026-08-03

### Summary
Resolved merge conflicts across dashboard reader/explorer pages, downloader package exports, and sentiment analysis test suite.

### Fixed
- Resolved merge conflicts in `src/storybuilder/dashboard/pages/read_story.py` and `search_explorer.py` by preserving `word_count` rendering.
- Retained `upload_sqlite_to_bigquery` export in `src/storybuilder/downloader/__init__.py`.
- Restored `find_multi_chapter_stories` test import in `tests/analysis/test_analyze_sentiment.py`.

## [PR-XXX](https://github.com/jgf-dev/story-builder/pull/XXX) - 2026-08-03

### Summary
Standardized GitHub Actions workflows to use GitHub-hosted runner labels.

### Fixed
- Replaced all `runs-on: Linux` entries with `runs-on: ubuntu-latest` in `.github/workflows/pylint.yml`, `.github/workflows/opencode.yml`, `.github/workflows/summary.yml`, and `.github/workflows/test.yml` to prevent jobs from remaining queued without a matching runner.
<<<<<<< HEAD

## [HASH](https://github.com/jgf2/story-builder/commit/HASH) - 2026-08-03

### Summary
Compacted `AGENTS.md` by consolidating duplicate layout/structure listings and grouping repository rules and workflows strictly by technical domain.

### Fixed
- Reduced `AGENTS.md` verbosity and token count by >55% while preserving all CLI flags, gotchas, prompt schemas, and environment rules.

=======
>>>>>>> origin/main
## [HASH](https://github.com/jgf2/story-builder/commit/HASH) - 2026-08-02

### Summary
Added BigQuery upload script `bq_upload.py` (`storybuilder-bq`) in `src/storybuilder/downloader` to stream/stage SQLite tables (including `stories/db/stories.db`) into Google BigQuery datasets.

### Added
- `src/storybuilder/downloader/bq_upload.py`: Batch NDJSON loader and GCS staging client for uploading SQLite tables to BigQuery.
- `storybuilder-bq` CLI entrypoint in `pyproject.toml`.
- Unit test suite `tests/downloader/test_bq_upload.py` covering schema mapping, batch chunking, NDJSON serialization, GCS staging, dry-run, and BigQuery client execution.
- Exported `upload_sqlite_to_bigquery` in `src/storybuilder/downloader/__init__.py`.

## [HASH](https://github.com/jgf2/story-builder/commit/HASH) - 2026-08-02


### Summary
Resolved merge conflicts across dashboard layout, ADK eval runner, accessibility palette, storage guard, and CI configuration.

### Fixed
- Resolved merge conflicts in `dashboard.html` by standardizing on `how-to-use-heading` and `how-to-use-desc` accessibility IDs.
- Resolved merge conflicts in `evals/run_adk_eval.py` by restoring `Path.cwd()`.
- Resolved merge conflicts in `.jules/palette.md` by retaining all updated accessibility guidelines.
- Preserved CircleCI test suite configuration and downloader storage `STORIES_DB` fail-fast validation.

## [PR-1619](https://github.com/jgf-dev/story-builder/pull/1619) - 2026-08-02

### Summary
Fail fast in the downloader storage script when `STORIES_DB` is unset.

### Fixed
- Raised a `ValueError` in `src/storybuilder/downloader/storage.py` instead of resolving an empty `STORIES_DB` value to the current working directory.

## [HASH](https://github.com/jgf2/story-builder/commit/HASH) - 2026-08-02

### Summary
Hardened CircleCI CLI installation to avoid piping an unpinned remote script into `sudo bash`.

### Fixed
- Replaced the CircleCI CLI install script pipe with a pinned release tarball download plus SHA256 verification in `.circleci/config.yml`.

## [PR-XXX](https://github.com/jgf2/story-builder/pull/XXX) - 2026-08-02

### Summary
Configured CircleCI Smarter Testing with `test-suites.yml` and updated `config.yml` to use `circleci testsuite run`.

### Added
- `.circleci/test-suites.yml` with `discover` (finds all `test_*.py` files), `run` (pytest with JUnit XML via `<< outputs.junit >>`), and `outputs.junit: test-reports`.
- CircleCI CLI install step in `config.yml`.
- `store_test_results` step in `config.yml` pointing to `test-reports`.

### Changed
- Replaced `uv run pytest` with `circleci testsuite run "ci tests"` in the CI test step.
## [c650177](https://github.com/jgf2/story-builder/commit/c650177) - 2026-08-01

### Summary
Resolved merge conflicts across `.jules/palette.md`, `evals/run_adk_eval.py`, `scripts/import_to_sqlite.py`, `src/storybuilder/downloader/network.py`, and `src/storybuilder/genai/client.py`.

### Fixed
- Restored `.jules/palette.md` accessibility learning notes.
- Resolved error handling exception type parameters in `evals/run_adk_eval.py`.
- Preserved default `force=False` in `scripts/import_to_sqlite.py` `_flush_batch`.
- Added complete type annotations for `fetch_page` in `src/storybuilder/downloader/network.py`.
- Preserved interaction ID continuity warning log in `src/storybuilder/genai/client.py`.

## [e805363](https://github.com/jgf2/story-builder/commit/e8053631ac47d693b5838a1e510a1dd4991abca5) - 2026-08-01

### Summary
Resolved merge conflict in `src/storybuilder/analysis/extract_entities.py` by reinstating `get_processed_files` with type annotations and O(1) set lookups, removing duplicate processed files checks, and formatting code with ruff.

### Fixed
- Resolved git merge conflict in `src/storybuilder/analysis/extract_entities.py`.
- Reinstated `get_processed_files(cursor: Cursor) -> set[str]` required by unit tests.
- Added type annotations to `init_db` and `load_spacy_model`.
- Fixed duplicate `processed_files` evaluation and O(N) DB query performance bottleneck.
## [PR-001](https://github.com/jgf2/story-builder/pull/001) - 2026-07-20

### Summary
Fixed SQLite import schema column mismatch in `scripts/import_to_sqlite.py` and applied hardening improvements to eval status parsing and GenAI client continuity warning logging.

### Added
- Added unit test in `tests/downloader/test_database.py` verifying `import_to_sqlite` batch execution against `db.init_db()` schema.
- Added unit test in `tests/genai/test_tts_pipeline.py` verifying warning logged when GenAI interaction response is missing `id` attribute.

### Fixed
- Fixed column mismatch in `scripts/import_to_sqlite.py` by removing obsolete `email_date` from SQL `INSERT OR REPLACE` query and batch tuple parameters.
- Hardened status conversion in `evals/run_adk_eval.py` by catching `TypeError` alongside `KeyError` and `ValueError`.
- Added explicit warning log in `src/storybuilder/genai/client.py` when `getattr(interaction, "id", None)` returns `None` to make session continuity loss observable.
- Resolved IDE type annotations, shebang file permissions, and code quality diagnostics across `src/storybuilder/genai/client.py`, `scripts/import_to_sqlite.py`, and `evals/run_adk_eval.py`.

## [PR-000](https://github.com/jgf2/story-builder/pull/000) - 2026-07-18

### Summary
Fixed Pyrefly check static type checker diagnostics and unresolved imports in the downloader, analysis, and test suites.

### Added
- Added `search-path` configuration to `pyproject.toml` under `[tool.pyrefly]` to resolve dynamic/relative script and test helper imports.

### Fixed
- Fixed type annotations for `all_story_targets` in `src/storybuilder/downloader/cli.py` to use `dict[tuple[str | None, str], dict]`.
- Resolved type diagnostics in `tests/downloader/test_cli.py` relating to index keys, `NoneType` checks, and `date` type narrowing.
- Resolved `None` subscriptable type issues in `tests/downloader/test_database.py` by adding type assertions.
- Fixed constant boolean value check in `tests/downloader/test_downloader.py` and updated test assertions.
- Fixed mock calls type checking in `tests/agents/test_subagent.py` and `tests/misc/test_keys.py` by casting mock client calls to `Any`.
- Fixed unused variable warning in `src/storybuilder/analysis/generate_embeddings.py`.
- Configured pytest in `pyproject.toml` to ignore third-party/system `DeprecationWarning`s to clean up test output.
>>>>>>> origin/known-quail-harlequin-831

## [c650177](https://github.com/jgf2/story-builder/commit/c650177) - 2026-08-01

### Summary
Resolved merge conflicts across `.jules/palette.md`, `evals/run_adk_eval.py`, `scripts/import_to_sqlite.py`, `src/storybuilder/downloader/network.py`, and `src/storybuilder/genai/client.py`.

### Fixed
- Restored `.jules/palette.md` accessibility learning notes.
- Resolved error handling exception type parameters in `evals/run_adk_eval.py`.
- Preserved default `force=False` in `scripts/import_to_sqlite.py` `_flush_batch`.
- Added complete type annotations for `fetch_page` in `src/storybuilder/downloader/network.py`.
- Preserved interaction ID continuity warning log in `src/storybuilder/genai/client.py`.

## [e805363](https://github.com/jgf2/story-builder/commit/e8053631ac47d693b5838a1e510a1dd4991abca5) - 2026-08-01

### Summary
Resolved merge conflict in `src/storybuilder/analysis/extract_entities.py` by reinstating `get_processed_files` with type annotations and O(1) set lookups, removing duplicate processed files checks, and formatting code with ruff.

### Fixed
- Resolved git merge conflict in `src/storybuilder/analysis/extract_entities.py`.
- Reinstated `get_processed_files(cursor: Cursor) -> set[str]` required by unit tests.
- Added type annotations to `init_db` and `load_spacy_model`.
- Fixed duplicate `processed_files` evaluation and O(N) DB query performance bottleneck.
## [PR-001](https://github.com/jgf2/story-builder/pull/001) - 2026-07-20

### Summary
Fixed SQLite import schema column mismatch in `scripts/import_to_sqlite.py` and applied hardening improvements to eval status parsing and GenAI client continuity warning logging.

### Added
- Added unit test in `tests/downloader/test_database.py` verifying `import_to_sqlite` batch execution against `db.init_db()` schema.
- Added unit test in `tests/genai/test_tts_pipeline.py` verifying warning logged when GenAI interaction response is missing `id` attribute.

### Fixed
- Fixed column mismatch in `scripts/import_to_sqlite.py` by removing obsolete `email_date` from SQL `INSERT OR REPLACE` query and batch tuple parameters.
- Hardened status conversion in `evals/run_adk_eval.py` by catching `TypeError` alongside `KeyError` and `ValueError`.
- Added explicit warning log in `src/storybuilder/genai/client.py` when `getattr(interaction, "id", None)` returns `None` to make session continuity loss observable.
- Resolved IDE type annotations, shebang file permissions, and code quality diagnostics across `src/storybuilder/genai/client.py`, `scripts/import_to_sqlite.py`, and `evals/run_adk_eval.py`.

## [PR-000](https://github.com/jgf2/story-builder/pull/000) - 2026-07-18

### Summary
Fixed Pyrefly check static type checker diagnostics and unresolved imports in the downloader, analysis, and test suites.

### Added
- Added `search-path` configuration to `pyproject.toml` under `[tool.pyrefly]` to resolve dynamic/relative script and test helper imports.

### Fixed
- Fixed type annotations for `all_story_targets` in `src/storybuilder/downloader/cli.py` to use `dict[tuple[str | None, str], dict]`.
- Resolved type diagnostics in `tests/downloader/test_cli.py` relating to index keys, `NoneType` checks, and `date` type narrowing.
- Resolved `None` subscriptable type issues in `tests/downloader/test_database.py` by adding type assertions.
- Fixed constant boolean value check in `tests/downloader/test_downloader.py` and updated test assertions.
- Fixed mock calls type checking in `tests/agents/test_subagent.py` and `tests/misc/test_keys.py` by casting mock client calls to `Any`.
- Fixed unused variable warning in `src/storybuilder/analysis/generate_embeddings.py`.
- Configured pytest in `pyproject.toml` to ignore third-party/system `DeprecationWarning`s to clean up test output.

## [PR-1392](https://github.com/jgf-dev/story-builder/pull/1392) - 2026-07-16

### Summary
Moved the `metadata_cache.json` cache file to the database folder (`stories/db/metadata_cache.json`) instead of keeping it in the downloaded stories directory (`stories/text/metadata_cache.json` or `nifty_stories/metadata_cache.json`).

### Added
- Standardized `stories/db/metadata_cache.json` as the default location for the scraper metadata cache.

### Removed
- Removed the old/duplicate `nifty_stories/metadata_cache.json` file.
- Removed the `stories/text/metadata_cache.json` cache file.

### Fixed
- Updated the cache location resolving logic in `src/storybuilder/downloader/cli.py` to target the parent directory of `args.db` or default to `stories/db`.
- Fixed the default cache location in `load_cache` and `save_cache` functions in `src/storybuilder/downloader/cache.py` to default to `stories/db`.
- Adjusted unit tests in `tests/downloader/test_cli.py` to assert the resolved cache directory logic properly.
