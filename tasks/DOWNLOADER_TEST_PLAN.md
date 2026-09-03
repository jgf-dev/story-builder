# Downloader Sub-Modules Test Coverage Improvement Plan

## Current State (latest run)

Downloader package: **65%** (was ~58%)

| Module                     | Coverage  | Notes                     |
|----------------------------|-----------|---------------------------|
| cli.py                     | 42%       | Major gap                 |
| scraper.py                 | 50%       | Major gap                 |
| storage.py                 | 72%       | Improved previously       |
| db.py                      | 74%       | Reasonable                |
| writer.py                  | 81%       | Good                      |
| network/cache/date_parser  | 85-88%    | Good                      |

## Strategy (following Testing Strategy skill)

- **Focus**: Unit tests for pure logic and critical paths.
- **Pyramid**: Many fast unit tests > fewer integration.
- **Prioritize**:
  - Business critical: date filtering, early-stop, cache decisions, subcategory discovery, duplicate handling.
  - Error/edge: bad HTML, invalid dates, empty results, "Dir" entries, Parent Directory, future dates.
- **Mocks**: Heavy use for network, cache, concurrency.
- **Skip for unit**: Full end-to-end web scraping (fragile + slow).

## Module Test Plans

### scraper.py (Target 70%+)

#### Unit tests with BeautifulSoup fixtures + mocks

High value uncovered areas:

- `_extract_subcategories_from_html` (primary + fallback)
- `_filter_subcategories`
- `_filter_stories_by_date` (dirs always kept, range filtering)
- `_merge_and_save_stories`
- `_get_cached_subcategory`
- Pagination / early stop logic (via mocks on `fetch_page` + `parse_listing_rows`)
- `scrape_multi_chapter_folder` helpers
- `process_subcategory` orchestration paths

Example test cases (implemented or planned):

- list-group vs raw link fallback HTML
- Mixed ftr + tr rows
- Early stop when story date < start_date (non-dir)
- Cache hit stops further pagination
- Directories ("Dir") bypass date filtering
- Merge prefers scraped over cached, sorts newest first

### cli.py (Target 60%+)

#### Unit tests on arg parsing + helpers

- `_parse_args` (required category, defaults, invalid)
- `_parse_dates` (good paths + bad formats)
- `_merge_targets` (deduplication of output_paths)
- `_setup_network` (already has good tests)
- Main flow + cloud upload (gcs/s3) with heavy patching

### Other Recommendations

- Add property-based or more exhaustive cases for date edge cases if needed.
- Consider a small set of integration tests for `process_subcategory` using recorded HTML (future).
- For DB: add tests for more complex search filters / entity_suffixes if coverage drops.
- Maintain fast feedback: keep new downloader tests under 5-10s total.

## Gaps Closed in This Iteration

- Added ~10+ new unit tests for scraper internals and CLI helpers.
- Improved scraper from 32% → 50%, cli 25% → 42%, package 58% → 65%.
- Focused on high-ROI pure functions rather than slow live network tests.

## Next Steps to Reach Higher Coverage

1. Mocked tests for `scrape_subcategory` / `process_subcategory` full paths.
2. More CLI main() paths (with `--force`, cloud flags, parallel).
3. Edge cases in multi-chapter folder handling.
4. Re-run full `uv run pytest --cov=src/storybuilder/downloader` after changes.

Run the downloader test suite:

```bash
uv run pytest tests/downloader/ -q
uv run coverage report --include="src/storybuilder/downloader/*"
```
