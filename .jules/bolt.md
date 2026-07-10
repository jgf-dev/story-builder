## 2026-06-22 - [Optimized Dashboard Favorites Loading]

**Learning:** In a multi-database partition architecture, rendering lists involving foreign keys or cross-references can inadvertently introduce massive N+1 issues when queries are done per row. The latency is multiplied by the number of partitions since we iterate over all year.db files for each row.
**Action:** Always batch cross-references up-front when resolving partitioned data. Use `IN (...)` queries in chunks per database to resolve all row dependencies at once before the rendering loop.

## 2026-06-25 - [Batching Dashboard Aggregations]

**Learning:** Initializing the Streamlit dashboard involves resolving global filter options (like all distinct authors and categories). Iterating over multi-partition database files using Python loops generates significant DB overhead.
**Action:** When aggregating data or executing queries across all partitioned SQLite databases, prefer using `storybuilder.downloader.db.execute_all_partitions` which leverages `ATTACH DATABASE` to batch operations, rather than manually iterating and opening connections per database file.

## 2026-06-25 - [Combining DISTINCT queries returns unique pairs]

**Learning:** Combining two `SELECT DISTINCT col1` and `SELECT DISTINCT col2` queries into a single `SELECT DISTINCT col1, col2` returns unique pairs, which can dramatically increase row count and memory usage compared to two separate queries.
**Action:** Do not combine `DISTINCT` queries for unrelated columns into a single pass if the goal is to get separate lists of unique values.

## 2026-06-26 - [Batching Stats Aggregation in Partitioned DB]

**Learning:** Performing multiple independent aggregations (like COUNT, SUM) sequentially using the multi-partition execution helper `storybuilder_db.execute_all_partitions` is O(N * M) where N is the number of aggregations and M is the number of partition DBs. This causes severe overhead since the helper has to repeatedly ATTACH and DETACH all databases for each query.
**Action:** Always combine related cross-partition aggregations into a single SQL pass (e.g. `SELECT COUNT(*), SUM(a), SUM(b) FROM {table}`) to minimize the number of partition traversals.

## 2026-06-27 - [SQL-Level Aggregation for Distributions]

**Learning:** Pulling large columns (like tens of thousands of `word_count` integers) into Python memory simply to generate distribution brackets using `pandas.cut` is a severe memory and performance bottleneck in the Streamlit dashboard.
**Action:** Push binning and aggregation logic down to the SQLite database using `CASE WHEN ... THEN ... GROUP BY`. This reduces data transfer and memory footprint from O(N) to O(1) bracket sizes while maintaining the exact same dashboard visualization output.

## 2026-06-28 - [Consolidating Cross-Partition Queries]

**Learning:** Making multiple `execute_all_partitions` calls for separate aggregations (like COUNT, SUM) is inefficient because it repeatedly opens connections and performs `ATTACH`/`DETACH` commands across partitioned databases. This leads to O(N * M) query overhead.
**Action:** Always combine related cross-partition aggregations into a single SQL pass (e.g., `SELECT COUNT(*), SUM(char_count), SUM(word_count) FROM {table}`) to minimize database operations and improve query performance.

## 2026-06-29 - [Parallelizing Cross-Partition SQLite Reads]

**Learning:** Sequentially looping over multiple SQLite partition databases to execute individual queries introduces a significant O(N) latency bottleneck, especially for search queries across many years. Since read queries in WAL-mode SQLite do not block each other, reading from independent partition files concurrently is completely safe.
**Action:** When querying separate SQLite partition databases (e.g. `search_all_partitions`), use `concurrent.futures.ThreadPoolExecutor` to map the read query across the database paths concurrently. This reduces execution latency from O(N) to O(1).
## 2026-07-08 - Concurrent Execution of Queries across SQLite Partitions
**Learning:** Sequential `ATTACH DATABASE` ... `DETACH DATABASE` for querying across independent SQLite partition files (like in `execute_all_partitions`) is an I/O bottleneck and doesn't scale well with the number of partitions. The codebase's architecture supports independent queries on each partition.
**Action:** Replace sequential looping with `concurrent.futures.ThreadPoolExecutor` opening independent connections to run queries concurrently. Always pass `check_same_thread=False` if not strictly required, wrap in `try/except sqlite3.OperationalError` for safety, and use a `finally` block to guarantee `conn.close()`.
