# Changelog

All notable changes to this project will be documented in this file.

## [HASH](https://github.com/jgf2/story-builder/commit/HASH) - 2026-08-02

### Summary
Resolved merge conflicts with `main` while preserving the PR's CI hardening and downloader storage guard.

### Fixed
- Resolved merge conflicts in `.circleci/config.yml`, `.circleci/test-suites.yml`, `.jules/palette.md`, `CHANGELOG.md`, and `src/storybuilder/downloader/storage.py`.
- Preserved the pinned CircleCI CLI install plus testsuite extension setup in `.circleci/config.yml`.
- Preserved the `STORIES_DB` fail-fast validation in `src/storybuilder/downloader/storage.py`.

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
