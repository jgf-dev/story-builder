# Changelog

All notable changes to this project will be documented in this file.

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
