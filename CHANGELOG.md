# Changelog

All notable changes to this project will be documented in this file.

## [e805363](https://github.com/jgf2/story-builder/commit/e8053631ac47d693b5838a1e510a1dd4991abca5) - 2026-08-01

### Summary
Resolved merge conflict in `src/storybuilder/analysis/extract_entities.py` by reinstating `get_processed_files` with type annotations and O(1) set lookups, removing duplicate processed files checks, and formatting code with ruff.

### Fixed
- Resolved git merge conflict in `src/storybuilder/analysis/extract_entities.py`.
- Reinstated `get_processed_files(cursor: Cursor) -> set[str]` required by unit tests.
- Added type annotations to `init_db` and `load_spacy_model`.
- Fixed duplicate `processed_files` evaluation and O(N) DB query performance bottleneck.

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
