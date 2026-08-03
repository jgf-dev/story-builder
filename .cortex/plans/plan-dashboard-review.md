# Plan: File Linear issues for dashboard findings + implement high-priority fixes

## Context

`scripts/dashboard.py` is a thin router delegating to the `storybuilder.dashboard`
package (`config`, `data`, `pages/*`, `ui/sidebar`). Code review surfaced 11
findings. User decisions: (1) tracker = **Linear** (team key `PRO`, title prefix
`GIT-`, GraphQL API); (2) file issues for **all** findings, then implement only
the **4 high-priority** fixes.

### Confirmed findings

**High (implement now):**
- **#1 Empty-DB stats crash** — `pages/archive_stats.py:17` does
  `df_years["Stories Count"].sum()`, but `data.load_archive_stats()` returns a
  bare `pd.DataFrame()` (no columns) when there is no DB connection
  (`data.py:129`) → `KeyError`.
- **#2 `execute_query` positional-param mismatch** — `downloader/db.py:382` calls
  `session.execute(text(sql), params)` with `params` a **tuple**. SQLAlchemy
  `text()` only binds named params (`:name`), not qmark `?`. The favorites batch
  query (`pages/favorites_tags.py:38-41`) passes `?` + a tuple, so it throws,
  is swallowed by the `except`, and every favorite silently defaults to year 2026.
- **#3 NULL `word_count` formatting** — `pages/search_explorer.py:53` and
  `pages/read_story.py:103` use `{...:,}` on `word_count`, which is nullable
  (confirmed in `tests/downloader/test_dashboard.py`) → `TypeError` on `None`.
- **#4 Malformed Markdown export** — `pages/read_story.py:85-94` builds the export
  string with ~20-space indentation inside a triple-quoted f-string; Markdown
  treats 4+ leading spaces as a code block, so the export renders as one code block.

**Medium (file issues only):**
- **#5** `scripts/dashboard.py:8-22` force-`importlib.reload` block recreates
  `@st.cache_*` functions every run, defeating caching.
- **#6** Test hooks leak into runtime: `config.get_*` read `sys.modules["dashboard"]`
  (`config.py:20-36`); entrypoint globals only work under that module name.
- **#7** Hardcoded `2026` as "current year" in `data.py:254`, `sidebar.py:45,58`,
  `favorites_tags.py:45,47,82`.

**Low (file one grouped "polish" issue):**
- **#8** `get_meta_conn()` runs `CREATE TABLE` every call (`data.py:39`).
- **#9** Redundant `st.query_params["nav_page"]` writes (`search_explorer.py:81`,
  `favorites_tags.py:88`).
- **#10** Full story rendered via `st.markdown` (`read_story.py:109`) misinterprets
  plain-text markdown chars.
- **#11** Bare `except Exception` in `data.py:340,181`.

### Linear mechanics (from `.github/prompts/linear-assistant.prompt.md`)
- Endpoint `https://api.linear.app/graphql`; header `Authorization: $LINEAR_API_KEY`.
- Title prefix `GIT-`; team key `PRO` (resolve teamId via `teams` query).
- `LINEAR_API_KEY` is not committed; check `cortex secret list` first, use inline
  injection `LINEAR_API_KEY="<key>" curl ...`; if absent, ask the user to add via
  `/secrets`. Never print the key.

## Implementation steps

### Step 1: File Linear issues for all findings
Resolve the `PRO` teamId, then create issues via GraphQL `issueCreate`, each title
prefixed `GIT-`, priority label reflecting High/Medium/Low. Group the 4 low findings
(#8-#11) into a single "dashboard polish" issue → **8 issues total** (4 high, 3
medium, 1 grouped). Search existing issues first to avoid duplicates. Report all URLs.

#### Context Sources
- Repo file `.github/prompts/linear-assistant.prompt.md` (lines 10, 24-32, 47-50):
  PRO team, `GIT-` prefix, GraphQL create mutation, key handling.
- Stored-secrets protocol: `cortex secret list` + inline injection; ask via `/secrets` if missing.

### Step 2: Fix #1 — empty-DB stats guard
In `src/storybuilder/dashboard/pages/archive_stats.py`, after `load_archive_stats()`,
if `df_years.empty` (or missing `Stories Count`), render `st.info("No archive data
available yet.")` and `return` before computing metrics/charts.

#### Context Sources
- `data.py:122-129`: returns empty `pd.DataFrame()` on no connection.
- `archive_stats.py:17-26`: unguarded `.sum()` / division.

### Step 3: Fix #2 — favorites year resolution without broken param path
In `src/storybuilder/dashboard/pages/favorites_tags.py:33-50`, replace the
`storybuilder_db.execute_query(sql, params=tuple(...))` call with a direct DBAPI
cursor obtained from `storybuilder_db.get_conn()` (sqlite3 natively supports `?`
qmark params), mirroring `data.get_story_by_path`. Do **not** modify
`downloader/db.py` `execute_query` (shared with the downloader; the no-param
`get_filter_options` path works). Keep the try/except fallback to year 2026.

#### Context Sources
- `db.py:371-387`: `execute_query` uses `text()` + tuple → incompatible with `?`.
- `db.py:324-342` pattern: `get_conn()` cursor with `?` params works.
- `favorites_tags.py:31-50`: current broken batch query.

### Step 4: Fix #3 — NULL word_count formatting
Coalesce to 0 before formatting: `search_explorer.py:53` →
`{(res.get("word_count") or 0):,}`; `read_story.py:103` → guard
`story.get("word_count") or 0`.

#### Context Sources
- `tests/downloader/test_dashboard.py:76-80`: `word_count` is optional/None.

### Step 5: Fix #4 — Markdown export formatting
In `src/storybuilder/dashboard/pages/read_story.py:85-94`, rebuild `md_content`
without leading indentation (join unindented lines or `textwrap.dedent`), so the
export is valid Markdown.

#### Context Sources
- `read_story.py:85-100`: indented f-string body feeding `st.download_button`.

### Step 6: Add regression tests
Add tests under `tests/downloader/` for the empty-stats render path (#1) and a
favorites query returning a valid year (#2). Follow existing `sys.modules["dashboard"]`
mock + `tempfile` patterns. Match ruff/black style (line-length 120, tab indent).

#### Context Sources
- `tests/downloader/test_dashboard.py:454-483` (`test_load_archive_stats`), `135`
  (`test_favorites_crud`): existing patterns to mirror.

## Verification
- `uv run pytest tests/downloader/test_dashboard.py tests/downloader/test_dashboard_streamlit.py`
- `uv run ruff check src/storybuilder/dashboard scripts/dashboard.py`
- Manual smoke: `streamlit run scripts/dashboard.py` → Archive Stats with no DB
  shows info (not crash); a favorite loads the reader; export produces clean `.md`.
- Confirm all 8 Linear issue URLs returned and titles carry `GIT-` prefix.

## Critical Files
- `src/storybuilder/dashboard/pages/archive_stats.py` — #1 crash guard.
- `src/storybuilder/dashboard/pages/favorites_tags.py` — #2 query rewrite.
- `src/storybuilder/dashboard/pages/read_story.py` — #3 + #4.
- `src/storybuilder/dashboard/pages/search_explorer.py` — #3.
- `src/storybuilder/downloader/db.py` — reference only; do NOT modify (shared).

## Team execution note
Plan-mode sandbox blocks `cortex ctx task add`, so the ctx step graph and
teammate spawns are created **after** plan approval: 1 implementor for Linear
issue-filing (Step 1, credentialed — general-purpose worker that runs
`cortex secret list` + inline injection), 1-2 implementors for the code fixes
(Steps 2-6), and 1 verifier (tests + ruff + diff review).
