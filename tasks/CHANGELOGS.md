# Changelog

## [2026-07-10] Merge Conflict Resolution
- Resolved merge conflicts in:
  - `scripts/dashboard.py` (kept HEAD comment explaining HTML/snippet highlighting)
  - `src/storybuilder/downloader/db.py` (kept HEAD multi-line ThreadPoolExecutor formatting)
  - `src/storybuilder/genai/client.py` (kept HEAD safety check for `transcript is None`)
- Ran full unit test suite; all 159 tests passed.
- Formatted and verified linting via Ruff on the modified files.
