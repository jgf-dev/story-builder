---
title: Storybuilder dev changelog
description: Explanation of changes per commits
---

## 11/07/2026

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

## 10/07/2026

### Resolved multi-branch merge conflicts (cloud-output-adapters + parallelize-partitions)

- **storage.py**: Merged both branches — adopted `upload_many_gcs` (renamed from `upload_many`) and added new `upload_many_s3` + `_upload_single_s3` from the cloud-output-adapters branch. Added type hints and docstrings.
- **test_split_prompts.py**: Updated mock target from `upload_many` to `upload_many_gcs` to match `cli.py` imports.
- **test_tts_pipeline.py**: Resolved 12 conflict regions — kept `get_gemini_api_keys` (matching current `client.py`), used `Path`-based operations, consistent variable naming (`configured_api_keys`, `completed_files`), and added return type hints.
- **db.py**: No conflict markers (already resolved), staged as-is.
- All 15 tests pass. Ran `ruff check --fix` (64 auto-fixes) and `ruff format`.

## 10/07/2026

### Resolved merge conflicts with palette/fix-duplicate-file-input

- Config files: Maintained local space indentation, dependency overrides (`sqlmodel`), and integrations (Linear, SonarLint) from HEAD.
- Monolithic DB preservation: Kept the monolithic database architecture (`stories.db`) and SQLModel refactoring from HEAD, rejecting the incoming branch's legacy database partitioning.
- Verified and formatted: All 169 unit tests passed successfully, and files were styled with `ruff format`.

### Resolved merge conflicts on branch implement-cloud-output-adapters

- dependencies: Merged updated project dependencies from HEAD with `boto3` support from the incoming branch to enable S3 storage adapters.
- dashboard layout: Kept the thin launcher design of `dashboard.py` from HEAD, removing duplicate legacy stats rendering blocks.
- tests and utility files: Resolved speech config test and storage utility conflicts by retaining GCS and S3 capability updates, completing the git merge smoothly.

## 04/07/2026
  
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

* **Result**: **169 passed successfully** (no failures).

### Code Quality

Ran static analysis and style checks:

```bash
uv run ruff check <resolved_files>
```

* **Result**: All resolved files are completely clean and lint-free.

## 10/07/2026

### Resolved Merge Conflicts between fix/summary-workflow-ai-improve-title and topic/cleanup

- **Monolithic Database Consolidation**: Maintained monolithic SQLModel database architecture (`stories.db`) and removed all year-partitioned database code conflicts from `db.py`, `story_db.py`, tests, and the Streamlit dashboard components.
- **Code Health Integrations**: Integrated the Edge debugging configurations in `.vscode/launch.json`, new ADK evaluation framework files under `evals/`, dependency updates (`streamlit>=1.59.0`, `tqdm>=4.68.4`), and clean path handling (`Path.stem` instead of `os.path`) in `test_tts_pipeline.py`.
- **Validation**: All 169 unit tests passed successfully.

Please refresh/reload your browser tab running the Streamlit app. This will force a script rerun, which now dynamically reloads all submodules, initializes the database partition engine, and displays the stories.
