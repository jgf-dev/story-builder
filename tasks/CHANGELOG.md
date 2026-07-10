---
title: Storybuilder dev changelog
description: Explanantion of changes per commits
---

## 04/07/2026
  
### restored the compatibility contract for the  {table}  formatting alias in  execute_all_partitions

- Restored ATTACH alias semantics: Updated the  execute_all_partitions  function in db.py to execute  ATTACH DATABASE ? AS curr_db  and format  {table}  as  curr_db.stories  when querying partition files.
- Monolithic consistency: Monolithic query paths still format  {table}  as  stories  (consistent with the legacy monolithic schema path).
- Fully Backward Compatible: This change satisfies any queries that expect or use the attached table alias (e.g. referencing other tables via  curr_db.*  or utilizing the qualified  curr_db.stories  identifier).

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
  concurrent reader connections).

### The reason the search results were not displaying is due to a **Streamlit module caching behavior**

### The Cause

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
