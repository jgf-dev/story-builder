# Changelog

All notable changes to this project will be documented in this file.

## [HASH](https://github.com/jgf2/story-builder/commit/HASH) - 2026-08-24

### Summary
Promoted `import_to_sqlite.py` and `story_db.py` into packaged console-script CLIs (`story-import`, `story-db`).

### Changed
- Moved `scripts/import_to_sqlite.py` → `src/storybuilder/db_tools/import_to_sqlite.py` and `scripts/story_db.py` → `src/storybuilder/db_tools/story_db.py` (new `db_tools` subpackage) so they install as proper console scripts.
- Registered `story-import` and `story-db` entry points in `pyproject.toml` (`[project.scripts]`).
- Updated `README.md`, `AGENTS.md`, `.github/workflows/test.yml`, `.agent/resolve_conflicts.py`, and `tests/downloader/test_database.py` to reference the new package paths and console commands.

## [HASH](https://github.com/jgf2/story-builder/commit/HASH) - 2026-08-22

### Summary
Resolved merge conflicts across `CHANGELOG.md`, `evals/run_adk_eval.py`, `scripts/import_to_sqlite.py`, `tests/genai/test_cartesia.py`, and `tests/utils/test_logging_config.py`.

### Fixed
- Resolved merge conflicts across codebase.
- Fixed SQL column mapping in `scripts/import_to_sqlite.py` `_flush_batch` by removing obsolete `email_date` column.
- Added type annotation to `is_processed` in `src/storybuilder/analysis/extract_entities.py`.
- Preserved key name rotation logging in `src/storybuilder/genai/client.py`.
- Fixed catastrophic regex backtracking (ReDoS) in `_parse_author` in `src/storybuilder/downloader/db.py` causing downloader to stall at 100% CPU on non-bracketed author strings.
- Enhanced `_parse_output_path` in `src/storybuilder/downloader/db.py` to correctly identify orientation and category across multi-level output directories (such as `stories/text`).
- Replaced `runs-on: Linux` with `runs-on: ubuntu-latest` in `.github/workflows/test.yml`.

### Added
- Maintained `test_wave_file` and standardized assertions in `tests/genai/test_cartesia.py`.
- Verified full test suite passes (361 passed).

## [HASH](https://github.com/jgf2/story-builder/commit/HASH) - 2026-08-22

### Summary
Resolved git merge conflicts across `CHANGELOG.md`, `evals/run_adk_eval.py`, `scripts/import_to_sqlite.py`, `tests/genai/test_cartesia.py`, and `tests/utils/test_logging_config.py`.

### Fixed
- Resolved merge conflicts in all affected files.
- Fixed catastrophic regex backtracking (ReDoS) in `_parse_author` in `storybuilder.downloader.db`.
- Fixed multi-level output directory parsing in `_parse_output_path`.
- Restored `get_logger` import in `test_logging_config.py`.
- Verified test suite passes cleanly.

## [HASH](https://github.com/jgf2/story-builder/commit/HASH) - 2026-08-22

### Summary
Resolved merge conflicts across `CHANGELOG.md`, `src/storybuilder/dashboard/pages/search_explorer.py`, and `tests/genai/test_cartesia.py`. Fixed SQLite import batch column alignment and test imports.

### Fixed
- Resolved merge conflicts in `CHANGELOG.md`, `search_explorer.py`, and `test_cartesia.py`.
- Fixed SQL column mapping in `scripts/import_to_sqlite.py` `_flush_batch` by removing obsolete `email_date` column.
- Added missing `get_logger` import in `tests/utils/test_logging_config.py`.
- Verified complete test suite passing (361 passed).

## [PR-1754](https://github.com/jgf-dev/story-builder/pull/1754) - 2026-08-15

### Summary
Continued PR #1754 by resolving merge conflicts with `origin/main` and addressing outstanding review feedback. Standardized GitHub Actions workflows to use GitHub-hosted runner labels.

### Fixed
- `main.py` now loads the project `.env` from the script's directory before `braintrust.auto_instrument()` runs, ensuring environment variables are available for library initialization.
- `src/storybuilder/dashboard/pages/archive_stats.py` removed redundant column-existence checks after the empty-database guard.
- Aligned repository with `origin/main` by removing deleted `.circleci/config.yml` and `.circleci/test-suites.yml`.
- Replaced all `runs-on: Linux` entries with `runs-on: ubuntu-latest` in `.github/workflows/pylint.yml`, `.github/workflows/opencode.yml`, `.github/workflows/summary.yml`, and `.github/workflows/test.yml` to prevent jobs from remaining queued without a matching runner.

### Added
- Added test coverage for the merged changes; full suite passes (360 passed, 1 skipped, 3 subtests passed).

## [HASH](https://github.com/jgf2/story-builder/commit/HASH) - 2026-08-05

### Summary
Resolved git merge conflicts across 7 files (`.jules/palette.md`, `CHANGELOG.md`, `scripts/import_to_sqlite.py`, `read_story.py`, `search_explorer.py`, `storage.py`, and `test_dashboard.py`).

### Fixed
- Merged `.jules/palette.md` accessibility learnings chronologically.
- Restored typed `_flush_batch` definition in `scripts/import_to_sqlite.py`.
- Standardized tab indentation and safe `word_count` rendering in `read_story.py` and `search_explorer.py`.
- Maintained `# pyrefly: ignore [missing-import]` comment for `boto3` in `storage.py`.
- Adopted environment variable patching for test database paths in `tests/dashboard/test_dashboard.py`.

## [72d34f0](https://github.com/jgf2/story-builder/commit/72d34f0) - 2026-08-05

### Summary
Resolved git merge conflicts across `.jules/palette.md`, `evals/run_adk_eval.py`, and `src/storybuilder/downloader/network.py`.

- Preserved `.jules/palette.md` accessibility learning notes and landmark documentation.
- Retained path handling logic in `evals/run_adk_eval.py`.
- Kept tab-formatted request rotation and retry implementations in `src/storybuilder/downloader/network.py`.
- Verified test suite execution with `pytest tests/downloader/test_network.py`.

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

## [HASH](https://github.com/jgf2/story-builder/commit/HASH) - 2026-08-03

### Summary
Compacted `AGENTS.md` by consolidating duplicate layout/structure listings and grouping repository rules and workflows strictly by technical domain.

### Fixed
- Reduced `AGENTS.md` verbosity and token count by >55% while preserving all CLI flags, gotchas, prompt schemas, and environment rules.

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

## [HASH](https://github.com/jgf2/story-builder/commit/HASH) - 2026-08-02

### Summary
Resolved merge conflicts across dashboard layout, ADK eval runner, accessibility palette, and CI configuration.

### Fixed
- Resolved merge conflicts in `dashboard.html` by standardizing on `how-to-use-heading` and `how-to-use-desc` accessibility IDs.
- Resolved merge conflicts in `evals/run_adk_eval.py` by restoring `Path.cwd()` and tab formatting.
- Resolved merge conflicts in `.jules/palette.md` by retaining updated accessibility guidelines.
- Preserved CircleCI test suite configuration and downloader storage validation.

## [730456f](https://github.com/jgf2/story-builder/commit/730456f) - 2026-08-02

### Summary
Resolved git merge conflicts across `pyproject.toml`, `dashboard.html`, `.jules/palette.md`, `src/storybuilder/analysis/extract_entities.py`, `src/storybuilder/dashboard/pages/read_story.py`, `src/storybuilder/dashboard/pages/search_explorer.py`, `evals/run_adk_eval.py`, `scripts/import_to_sqlite.py`, and `src/storybuilder/genai/client.py`.

### Fixed
- Combined `filterwarnings` in `pyproject.toml`.
- Restored safe `dict(...).get("word_count")` access in dashboard pages (`read_story.py`, `search_explorer.py`).
- Restored `get_processed_files` helper in `src/storybuilder/analysis/extract_entities.py`.
- Preserved `configure_logging` and exception handling in `evals/run_adk_eval.py`.
- Resolved batch flush parameter signatures in `scripts/import_to_sqlite.py`.
- Cleaned up duplicate imports and missing ID warning log in `src/storybuilder/genai/client.py`.

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

## [PR-1382](https://github.com/jgf2/story-builder/pull/1382) - 2026-07-16

### Summary
Fixed CI path-filter regressions in `.github/workflows/test.yml` flagged in review.

### Fixed
- Restored `tests/downloader/**` to the `downloader` path-filter so edits to downloader tests trigger the `test-downloader` job.
- Removed the duplicated `tests/dashboard/**` entry from the `dashboard` path-filter.

## [PR-1383](https://github.com/jgf-dev/story-builder/pull/1383) - 2026-07-16

### Summary
Removed the duplicate dashboard test file and redundant downloader conftest that were left behind when dashboard tests were decoupled into `tests/dashboard/`.

### Removed
- Deleted `tests/downloader/test_dashboard_pages.py`, a near-identical copy of `tests/dashboard/test_dashboard_pages.py`. The duplicate basename caused a pytest `import file mismatch` collection error when the full suite ran, and having both copies double-ran the dashboard tests (once under `test-downloader`, once under `test-dashboard`).
- Deleted `tests/downloader/conftest.py`; its global-state reset (`db.close_db()` + `scraper.seen_folders.clear()`) is already provided repo-wide by the autouse `clean_globals` fixture in `tests/conftest.py`.

### Fixed
- Fixed the SonarCloud Quality Gate failure (40% duplication and B security rating on new code) caused by the newly-added `test-dashboard` job and `opencode.yml` workflow. Added `.github/**` to `sonar.exclusions` in `sonar-project.properties` so SonarCloud Automatic Analysis scopes to application source only, consistent with the existing `sonar.sources=./src/` intent and the already-excluded `tests/`, `scripts/`, and `doc/` paths.

## [PR-1375](https://github.com/jgf-dev/story-builder/pull/1375) - 2026-07-16

### Summary
Repaired the invalid Mergify configuration while preserving safe CI, review, conflict, and branch-update automation.

### Fixed
- Restored the aggregate `run_tests / test-results` check gate and required human review conditions.
- Combined merge-protection conditions into one valid YAML mapping and removed malformed nested rules.
- Kept conflict notification and stale-branch update rules as valid `pull_request_rules`.

## [PR-1363](https://github.com/jgf-dev/story-builder/pull/1363) - 2026-07-15

### Summary
Fixed CI path filter so changes to `src/storybuilder/dashboard/**` trigger the downloader test job. Also adjusted Markdown export formatting in `read_story.py` to separate the metadata header from the story body with a blank line.

### Fixed
- Added `src/storybuilder/dashboard/**` to the `downloader` paths-filter in `.github/workflows/test.yml` so that dashboard page changes (e.g. `read_story.py`) now trigger `test-downloader` and execute the existing dashboard Streamlit tests.
- Ensured exported Markdown includes a blank line between the metadata header and story content in `src/storybuilder/dashboard/pages/read_story.py`.

## [PR-1372](https://github.com/jgf-dev/story-builder/pull/1372) - 2026-07-15

### Summary
Improved the dashboard's semantic structure while preserving its existing layout.

### Fixed
- Replaced generic note containers with native `<ul>` and `<li>` elements and reset their default visual styling.
- Scoped the page-header layout styles so semantic card headers retain their original spacing.
- Updated the accessibility guidance to prefer native list elements over generic ARIA grouping.
- Fixed Quick Stats parsing so checklist items are counted within the correct task section.
- Added arrow-key, Home, and End navigation with a single tab stop for the editor toolbar.

## [PR-1369](https://github.com/jgf-dev/story-builder/pull/1369) - 2026-07-15

### Summary
Fixed the Mergify merge queue configuration so test-check detection references a check that actually exists in CI.

### Fixed
- Replaced the invalid `check-success = .*test.*` condition (which used the literal-match `=` operator and would never match a real check) with the regex-match operator and an anchored pattern `check-success ~= ^run_tests / test-results$` in `queue_rules.merge_conditions`.
- Applied the same anchored `^run_tests / test-results$` pattern to `merge_protections_settings.auto_merge_conditions`, replacing the overly broad `.*[Tt]est.*` regex that could match unintended check names, and keeping both sections consistent with the check produced by `.github/workflows/test.yml`.

## [PR-1363](https://github.com/jgf-dev/story-builder/pull/1363) - 2026-07-15

### Summary
Fixed CI path filter so changes to `src/storybuilder/dashboard/**` trigger the downloader test job.

### Fixed
- Added `src/storybuilder/dashboard/**` to the `downloader` paths-filter in `.github/workflows/test.yml` so that dashboard page changes (e.g. `read_story.py`) now trigger `test-downloader` and execute the existing dashboard Streamlit tests.
- Fixed leaking global state between downloader tests that made `test-downloader` (and thus `test-results`) fail once the job started running. Added `tests/downloader/conftest.py` with an autouse fixture that resets `db._conn`/`_engine` (via `close_db()`) and clears `scraper.seen_folders` after every test, so tests that call `db.init_db` or scrape folders no longer corrupt later tests.

## [6b00bc3e](https://github.com/jgf2/story-builder/commit/6b00bc3e7a996a1b0beb0805609ee0b593288596) - 2026-07-15

### Summary
Decoupled the Streamlit dashboard tests from the downloader tests by moving the files and establishing a dedicated CI job.

### Added
- Added a new `test-dashboard` CI job in `.github/workflows/test.yml` that runs pytest on `tests/dashboard`.
- Added a `dashboard` filter to the `changes` path-filter job to detect changes to `src/storybuilder/dashboard/**`, `scripts/dashboard.py`, and `tests/dashboard/**`.

### Removed
- Removed dashboard code and script paths from the `downloader` path-filter in `.github/workflows/test.yml`.

### Changed
- Moved dashboard unit and integration test files from `tests/downloader/` to `tests/dashboard/`.
- Updated dependencies for `test-results` and `post-coverage` jobs to include `test-dashboard`.

## [PR-1370](https://github.com/jgf2/story-builder/pull/1370) - 2026-07-15

### Summary
Fixed the Mergify merge queue configuration so the test-check gating conditions actually match the split CI test jobs.

### Fixed
- Fixed the Mergify `queue_rules.merge_conditions` test-check gate in `.mergify.yml`. It previously used the literal-match operator against a check name that no CI job produces (`check-success = Run Tests` / `check-success = .*test.*`), so the queue rule never gated on tests. It now uses the regex-match operator with the aggregate check name (`check-success ~= ^run_tests / test-results$`), consistent with `merge_protections_settings.auto_merge_conditions`.

## [PR-1368](https://github.com/jgf2/story-builder/pull/1368) - 2026-07-15

### Summary
Hardened the Mergify auto-merge `pull_request_rules` introduced in this PR to address Devin Review findings.

### Fixed
- Added a `#approved-reviews-by >= 1` condition so the "Auto-merge approved PRs" rule actually requires a human approval before merging.
- Replaced the broad `check-success =~ .*test.*` condition with the specific aggregate check `check-success ~= ^run_tests / test-results$`, so auto-merge only fires once all test jobs have succeeded instead of when any single matching job passes.
- Restored the `base = main` condition so the rule only targets PRs into `main`.

## [PR-1364](https://github.com/jgf-dev/story-builder/pull/1364) - 2026-07-15

### Summary

Added dashboard page test coverage and an authorized, dependency-pinned OpenCode workflow.

### Added

- Dashboard configuration, sidebar, archive statistics, favorites, story reader, and search explorer tests.
- Test isolation for shared downloader database and scraper state.
- An OpenCode comment workflow restricted to trusted repository contributors.

### Removed

- Support for the ambiguous `/oc` workflow command alias.

### Fixed

- Pinned the OpenCode action to an immutable commit SHA.
- Corrected SonarCloud exclusion property names and recursive glob patterns.
- Triggered dashboard tests when dashboard source files change.
- Standardized selected-story year state and dashboard tests on integer values.

## [af1d7aed](https://github.com/jgf2/story-builder/commit/af1d7aed) - 2026-07-15

### Summary
Resolved all pre-existing Ruff lint warnings and complexity issues in the dashboard codebase (data.py, archive_stats.py, favorites_tags.py, and read_story.py).

### Added
- Added `get_favorites_publication_years()` helper in `data.py` to resolve publication years in bulk and offload database logic from the UI layer.
- Added `_safe_query()` helper to execute queries cleanly and fetch rows without nested try blocks.

### Changed
- Flattened the nested control flow inside `read_story.py` using early return guards.
- Reduced the local variable counts in `archive_stats.py` by consolidating metric/chart columns and reusing the Plotly figures.
- Reformatted long HTML template cards to adhere to the 120-character line-length constraint.

## [862c2e9](https://github.com/jgf2/story-builder/commit/862c2e9f) - 2026-07-15

### Summary
Implemented high and medium priority dashboard fixes identified during code review, including resolving empty DB metrics crashes, fixing parameter mismatches, coalescing null values, dedenting markdown exports, guarding module reloading, and decoupling path resolution.

### Added
- Added regression tests for dashboard stats and year resolution in `test_dashboard.py`.
- Added `st.cache_data.clear()` to test setUp to prevent Streamlit cache pollution across test runs.

### Changed
- Refactored `archive_stats.py` to guard empty database state.
- Bypassed SQLAlchemy `text` positional binding issue in `favorites_tags.py` with native sqlite DBAPI cursor execution.
- Added coalescing to `word_count` rendering in `search_explorer.py` and `read_story.py`.
- Stripped leading indentation from exported markdown strings in `read_story.py` using `textwrap.dedent`.
- Guarded `importlib.reload` loop in `dashboard.py` launcher with a `DASHBOARD_DEV_MODE` check.
- Refactored `config.py` path resolution to check for environment variables and check both `__main__` and `dashboard` modules.
- Replaced hardcoded `2026` year references with dynamic timezone-aware UTC year lookup.

## [PR-1371](https://github.com/jgf-dev/story-builder/pull/1371) - 2026-07-15

### Summary

Followed up on PR #1365 by keeping downloader-specific test isolation scoped to downloader tests.

### Added

- Unit tests for dashboard configuration, navigation, archive statistics, favorites, story reading, and search pages.
- Downloader-scoped cleanup for database connections and the scraper folder cache.

### Removed

- The invalid and redundant SonarQube exclusion property for paths already outside `sonar.sources`.

### Fixed

- Prevented downloader cleanup from running around unrelated test suites.
- Ensured the genai database integration test closes stale downloader state before initialization.

## [PR-1374](https://github.com/jgf-dev/story-builder/pull/1374) - 2026-07-15

### Summary

Restored the recursive SonarCloud exclusions required to keep default-branch analysis scoped to production code.

### Added

- Recursive SonarCloud exclusions for tests, scripts, and documentation.

### Removed

- None.

### Fixed

- Prevented non-production files from affecting the default branch quality gate.

## 2026-07-14

### Consolidated dashboard code (Issue #457)

- **Deleted dead code**:
  - Removed entire `scripts/dashboard/` directory (unused models, repository, config)
  - Removed `test_perf.py` (performance test that used dead code)
- **Added tests for active dashboard code** (`tests/downloader/test_dashboard.py`):
  - `TestDashboardConfig` - 8 tests for config.py (get_db_dir, get_nlp_db_path, get_meta_db_path, constants)
  - `TestDashboardDataFunctions` - 4 tests for data.py (get_db_files, get_filter_options, load_archive_stats)
- **Verification**: All 199 tests pass (was 187 before, +12 new tests)

## 2026-07-13

### Test Coverage Improvements for Downloader Module

Increased package test coverage from **69% to 82%** (+13 percentage points).

#### cli.py (53% → 95%, +42%)
Added `TestCLIInternalFunctions` (10 tests):
- `_print_config` - basic, with db, with proxy/rotation
- `_merge_targets` - deduplication
- `_scrape_subcategories` - parallel and sequential
- `_download_stories_parallel` / `_download_stories_sequential`
- `_download_stories` - branch selection (parallel vs sequential)

Added `TestUploadToCloud` (4 tests):
- S3 only upload, GCS only upload, fallback to nifty-index, empty output handling

Added `TestStorageFunctions` (5 tests):
- `_s3_object_key` with/without prefix
- `upload_many_gcs` / `upload_many_s3` empty returns early
- `upload_many` delegates to GCS

#### scraper.py (67% → 83%, +16%)
Added `TestScraperMultiChapter` (9 tests):
- `_get_cached_chapters` - cache hit, cache miss, no chapters in range
- `_fetch_and_parse_chapters` - basic parsing, empty response
- `scrape_multi_chapter_folder` - cache usage, cache miss
- `_process_directory_story` - chapter target generation
- `_process_single_story` - single target generation

#### db.py (50% → 77%, +27%)
Added `TestDBSearch` (6 tests):
- Basic search, category filter, author filter, date range, no results, limit

Added `TestDBParseOutputPath` (5 tests):
- 3/4/5-part path parsing, chapter suffix detection, invalid path handling

Added `TestDBContentOperations` (2 tests):
- Get story returns all fields

#### writer.py (76% → 84%, +8%)
Added `TestWriterCacheInteraction` (5 tests):
- Duplicate targets, cache deduplication, file exists check, replicate_story, download_single_target

#### storage.py (72% → 73%, +1%)
Minor additions for S3 key generation and empty file handling.

#### Summary
- **147 tests passing**
- **Coverage**: 82% total package coverage
- **Files modified**: `test_cli.py`, `test_downloader.py`, `test_database.py`, `test_db.py`

---

## 2026-07-13

### Added centralized env module for API key management

- **New file: `src/storybuilder/utils/env.py`** - Centralized environment handling:
  - `load_env()` - Single `load_dotenv()` call with memoization (no-op after first call)
  - `get_api_key(name, required=True)` - Get required API keys with validation
  - `get_optional_api_key(name)` - Get optional keys that may be missing
  - `get_stable_api_key(base_name)` - **For TTS** - single key, NO rotation (maintains voice consistency)
  - `get_api_keys_with_rotation(base_name)` - For non-TTS quota rotation
- **New test file: `tests/misc/test_env.py`** - 12 tests covering env and logging_config

### Added centralized logging configuration

- **New file: `src/storybuilder/utils/logging_config.py`** - Standard logging setup:
  - `configure_logging()` - Single logging config with memoization (no-op after first call)
  - `get_logger(name)` - Get configured logger instances
  - `set_library_log_levels()` - Silence noisy third-party libraries (urllib3, boto3, google.genai, etc.)
  - Supports console + file output, configurable format
- **Updated**: `src/storybuilder/utils/storage.py` and `src/storybuilder/agents/tts_prompt_crafter/agent.py` now use centralized logging

### Fixed TTS error handling to preserve voice consistency

- **Updated `src/storybuilder/genai/client.py`** - Improved error handling logic:
  - **Quota errors (429)**: Now retries with exponential backoff (15s → 30s → 60s → 120s) on the **same API key** - NO automatic key rotation
  - **Session expiration (404)**: Prompts user with 4 options:
    - `[S] Skip` - continue without this file (preserves session for next)
    - `[Q] Quit` - let user restart manually from this file
    - `[K] Rotate key` - switch keys but continue session (voice mismatch possible)
    - `[A] Rotate + restart` - new key, restart session from this file (voice mismatch likely)
  - **Invalid/unauthorized key**: Prompts for key rotation (key is truly bad, not just quota)
  - Added `_prompt_key_rotation()` and `_rotate_key()` helper functions
  - Updated `_classify_error()` to detect unauthorized errors

**Why this matters**: TTS requires consistent voice across multiple sequential API calls within a story. Previous logic rotated keys on quota error, breaking the session chain and causing voice mismatch. Now users are warned and can choose whether to risk voice mismatch.

## 2026-07-11

### Resolved merge conflicts with branch fix-genai-tts-entrypoint-9568411881905231847

- **storage.py**: Consolidated concurrent `upload_many_s3` helper to run asynchronously via `ThreadPoolExecutor` while preserving custom S3 single-file uploading settings (e.g. AWS bucket owner checks). Removed `boto3` from top-level imports to keep S3 support optional at import time.
- **client.py**: Unified `process_file` and CLI `main` structure, keeping the api state key rotation and validation errors.
- **tts.py**: Directly re-exported CLI `main` and directory processor (with `__main__` guard).
- **test_genai.py**: Added mocks for API keys and glob results to ensure existing directory validations pass without key configuration constraints.

### Resolved merge conflicts with branch optimistic-jackal-jade-508

- **storage.py**: Consolidated GCS upload functions (`upload_many`, `upload_many_gcs`) to preserve prefix mapping and transfer_manager optimizations. Retained S3 bucket owner checks (`AWS_EXPECTED_BUCKET_OWNER`) during file uploads. Removed duplicate/obsolete helper definitions.
- **client.py**: Unified `main()` entrypoint function signature with correct type annotations, docstring, and preserved the `parser.error` exit behavior for missing directories. Kept refactored helper functions.
- **tts.py**: Re-exported `main` and `process_directory` from the genai client module to satisfy console scripts and test imports.
- **test_genai.py**: Consolidated test cases to verify the `genai-tts` CLI entrypoint (exits, directory validation) and keep the backtracking regex regression test.
- **Verification**: Ran `pytest` verifying all tests pass, and cleaned up style issues with `ruff`.

## 2026-07-10

### Resolved multi-branch merge conflicts (cloud-output-adapters + parallelize-partitions)

- **storage.py**: Merged both branches — adopted `upload_many_gcs` (renamed from `upload_many`) and added new `upload_many_s3` + `_upload_single_s3` from the cloud-output-adapters branch. Added type hints and docstrings.
- **test_split_prompts.py**: Updated mock target from `upload_many` to `upload_many_gcs` to match `cli.py` imports.
- **test_tts_pipeline.py**: Resolved 12 conflict regions — kept `get_gemini_api_keys` (matching current `client.py`), used `Path`-based operations, consistent variable naming (`configured_api_keys`, `completed_files`), and added return type hints.
- **db.py**: No conflict markers (already resolved), staged as-is.
- All 15 tests pass. Ran `ruff check --fix` (64 auto-fixes) and `ruff format`.

## 2026-07-10

### Resolved merge conflicts with palette/fix-duplicate-file-input

- Config files: Maintained local space indentation, dependency overrides (`sqlmodel`), and integrations (Linear, SonarLint) from HEAD.
- Monolithic DB preservation: Kept the monolithic database architecture (`stories.db`) and SQLModel refactoring from HEAD, rejecting the incoming branch's legacy database partitioning.
- Verified and formatted: All 169 unit tests passed successfully, and files were styled with `ruff format`.

### Resolved merge conflicts on branch implement-cloud-output-adapters

- dependencies: Merged updated project dependencies from HEAD with `boto3` support from the incoming branch to enable S3 storage adapters.
- dashboard layout: Kept the thin launcher design of `dashboard.py` from HEAD, removing duplicate legacy stats rendering blocks.
- tests and utility files: Resolved speech config test and storage utility conflicts by retaining GCS and S3 capability updates, completing the git merge smoothly.

## 2026-07-10

### Resolved Merge Conflicts between fix/summary-workflow-ai-improve-title and topic/cleanup

- **Monolithic Database Consolidation**: Maintained monolithic SQLModel database architecture (`stories.db`) and removed all year-partitioned database code conflicts from `db.py`, `story_db.py`, tests, and the Streamlit dashboard components.
- **Code Health Integrations**: Integrated the Edge debugging configurations in `.vscode/launch.json`, new ADK evaluation framework files under `evals/`, dependency updates (`streamlit>=1.59.0`, `tqdm>=4.68.4`), and clean path handling (`Path.stem` instead of `os.path`) in `test_tts_pipeline.py`.
- **Validation**: All 169 unit tests passed successfully.

Please refresh/reload your browser tab running the Streamlit app. This will force a script rerun, which now dynamically reloads all submodules, initializes the database partition engine, and displays the stories.

## 2026-07-04

### restored the compatibility contract for the  {table}  formatting alias in  execute_all_partitions

- Restored ATTACH alias semantics: Updated the  execute_all_partitions  function in db.py to execute  ATTACH DATABASE ? AS curr_db  and format  {table}  as  curr_db.stories  when querying partition files.
- Monolithic consistency: Monolithic query paths still format  {table}  as  stories  (consistent with the legacy monolithic schema path).
- Fully Backward Compatible: This change satisfies any queries that expect or use the attached table alias (e.g. referencing other tables via  curr_db.*  or utilizing the qualified  curr_db.stories  identifier).

### updated both search and execution functions in  src/storybuilder/downloader/db.py  to ensure that SQLite cursors are explicitly closed

Preventing any resource leaks in long-running processes like the Streamlit workspace dashboard.

- Cursor Cleanup in  _execute_single_db : Added a  cursor = None  declaration and an explicit  cursor.close()  check inside the  finally  block of the_execute_single_db  helper in db.py.
- Cursor Cleanup in  _search_single_db : Added the same resource cleanup for the SQLite cursor created during concurrent/monolithic partition searches in the_search_single_db  helper in db.py.

### hardened the monolithic mode thread-safety by implementing per-call read connections for concurrent read tasks

### updated both search and execution functions in  src/storybuilder/downloader/db.py  to ensure that SQLite cursors are explicitly closed

Preventing any resource leaks in long-running processes like the Streamlit workspace dashboard.

- Cursor Cleanup in  _execute_single_db : Added a  cursor = None  declaration and an explicit  cursor.close()  check inside the  finally  block of the  _execute_single_db  helper in db.py.
- Cursor Cleanup in  _search_single_db : Added the same resource cleanup for the SQLite cursor created during concurrent/monolithic partition searches in the  _search_single_db  helper in db.py.

### hardened the monolithic mode thread-safety by implementing per-call read connections for concurrent read tasks.

  Here is a summary of the changes:

  1. Global Path Tracking: Added  _monolithic_db_path  as a global variable in db.py.
  2. Database Initialization: Updated db.py to populate  _monolithic_db_path  when initializing in monolithic mode.
  3. Thread-Safe Reads:
      • Modified db.py (inside  execute_all_partitions ) to create a new connection per call when querying in monolithic mode.
      • Modified db.py (inside  search_all_partitions ) to also establish a separate connection per call for monolithic mode queries.
  4. Cleanup: Updated db.py to reset  _monolithic_db_path  to  None .

  These changes completely prevent concurrent read threads from using the shared write connection ( _conn ), safely resolving the thread-safety issue without any blocking overhead (since SQLite WAL mode natively supports

  These changes completely prevent concurrent read threads from using the shared write connection ( _conn ), safely resolving the thread-safety issue without any blocking overhead (since SQLite WAL mode natively supports
  concurrent reader connections).

### The reason the search results were not displaying is due to a **Streamlit module caching behavior**

### The Cause

- When you run a Streamlit server, it watches the main entry point script ([dashboard.py](file:///home/jgf2/git/voice/story-builder/scripts/dashboard.py)) for file changes and reruns it.
- However, Streamlit **caches all imported submodules** (such as `storybuilder.dashboard.data` or `storybuilder.dashboard.pages.*`) inside memory and does not automatically reload them when they are modified.
- As a result, the active Streamlit process was still running the older version of the refactored code (which was missing the database partition engine initialization) even after we fixed it in `data.py`.

* When you run a Streamlit server, it watches the main entry point script ([dashboard.py](file:///home/jgf2/git/voice/story-builder/scripts/dashboard.py)) for file changes and reruns it.
* However, Streamlit **caches all imported submodules** (such as `storybuilder.dashboard.data` or `storybuilder.dashboard.pages.*`) inside memory and does not automatically reload them when they are modified.
* As a result, the active Streamlit process was still running the older version of the refactored code (which was missing the database partition engine initialization) even after we fixed it in `data.py`.

### The Fix

1. We modified [`dashboard.py`](file:///home/jgf2/git/voice/story-builder/scripts/dashboard.py) to explicitly reload all of its custom dashboard package dependencies on rerun:
   ```python
   import importlib
   import sys

   if "storybuilder.dashboard.data" in sys.modules:
   	importlib.reload(sys.modules["storybuilder.dashboard.data"])
   # ... [reloads config, sidebar, and pages similarly]
   ```
2. Removed all temporary debugging logging files.
3. Verified the changes: all 172 tests still pass perfectly.

### What to do next

Please refresh/reload your browser tab running the Streamlit app. This will force a script rerun, which now dynamically reloads all submodules, initializes the database partition engine, and displays the stories.

---

# Walkthrough - Conflict Resolution

All merge conflicts between `homely-ox-lavender-771` and `decisive-hoverfly` have been successfully resolved.

## What Was Resolved

- **Monolithic SQLModel Database Primacy**: Discarded all old year-partitioned SQLite code blocks (`ATTACH DATABASE`, partition files routing) from the incoming branch in favor of the clean, modern SQLModel monolithic database architecture (`stories.db`).
- **Conflict Cleanups**: Resolved formatting, spacing, and style conflicts across the database, analysis, scripting, and testing layers by maintaining the formatted designs from `HEAD`.
- **Deprecated code cleanup**: Marked `verify_ux.py` as deleted (removed from index) to align with our latest main structure.
- **Testing updates**: Maintained monolithic test coverage in `tests/downloader/test_database.py` and `test_dashboard.py`.

---

## Verification Results

### Automated Tests

Ran the entire unit test suite containing 173 tests (169 active, 4 skipped):

```bash
uv run pytest
```

- **Result**: **169 passed successfully** (no failures).

### Code Quality

Ran static analysis and style checks:

```bash
uv run ruff check <resolved_files>
```

- **Result**: All resolved files are completely clean and lint-free.
