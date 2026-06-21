1. **Fix `len(db_paths) > 1` logic**:
   - Update `cmd_search`, `cmd_get`, `cmd_list`, `cmd_stats` in `scripts/story_db.py`.
   - The condition `if db_paths and len(db_paths) > 1:` was causing the logic to fall through to the `else` branch (which queries `conn` directly) when `len(db_paths) == 1`. Since `conn` is now a `:memory:` database, this will crash with `no such table: stories`.
   - Change the condition to `if db_paths:` so it always uses the dynamic ATTACH logic when multiple DBs are possible (i.e. `db_dir` is used).
2. **Restore `src/storybuilder/__init__.py`**:
   - The review noted that emptying `__init__.py` breaks the public API. I should restore the imports in `__init__.py` and fix the actual root cause of the `ImportError` in the test execution environment, if there is one. Wait, earlier I reverted `__init__.py` and the tests passed! So I just leave `__init__.py` as is (with imports) and I don't need to change it.
3. **Verify changes**:
   - Run `uv run pytest tests/test_database.py`.
