## 2026-06-19 - Combine SQL aggregations
**Learning:** Combining distinct SELECT aggregate queries (COUNT, SUM) into a single query in SQLite drastically reduces execution time by avoiding multiple full table scans.
**Action:** Always combine aggregate queries against the same table when retrieving basic stat blocks.
