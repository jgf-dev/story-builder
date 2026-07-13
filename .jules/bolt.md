## 2026-06-19 - Combine SQL aggregations
**Learning:** Combining distinct SELECT aggregate queries (COUNT, SUM) into a single query in SQLite drastically reduces execution time by avoiding multiple full table scans.
**Action:** Always combine aggregate queries against the same table when retrieving basic stat blocks.

## 2025-02-12 - Combine Aggregate Queries
**Learning:** Combining distinct SELECT aggregate queries (like `COUNT(*)` and `SUM()`) with `COUNT(DISTINCT NULLIF(col, ''))` into a single query in SQLite drastically reduces execution time by avoiding multiple full table scans. While `SELECT DISTINCT col1, col2` queries for independent items can explode row count, aggregating them into one query line like `SELECT COUNT(DISTINCT col1), COUNT(DISTINCT col2)` works correctly and provides major speedups without creating unique pairs.
**Action:** Always combine aggregate queries against the same table when retrieving basic stat blocks.
