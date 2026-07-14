## 2026-06-19 - Combine SQL aggregations
**Learning:** Combining distinct SELECT aggregate queries (COUNT, SUM) into a single query in SQLite drastically reduces execution time by avoiding multiple full table scans.
**Action:** Always combine aggregate queries against the same table when retrieving basic stat blocks.

## 2026-06-19 - Batch retrieve child entities for search results
**Learning:** Sequential N+1 SQL queries within a mapped row converter (like querying tags for each story row individually) degrades performance at scale (e.g. for page size >= 50).
**Action:** Pre-fetch all related tags or child entities for the fetched chunk of rows via an `IN (?, ?, ...)` clause to avoid sequential database hits. Ensure `sqlite3.Row` gets cast to a standard `dict` when injecting data like `.get()` since `Row` objects lack native `.get()` support.
