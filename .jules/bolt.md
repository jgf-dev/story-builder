## 2026-06-22 - [Optimized Dashboard Favorites Loading]
**Learning:** In a multi-database partition architecture, rendering lists involving foreign keys or cross-references can inadvertently introduce massive N+1 issues when queries are done per row. The latency is multiplied by the number of partitions since we iterate over all year.db files for each row.
**Action:** Always batch cross-references up-front when resolving partitioned data. Use `IN (...)` queries in chunks per database to resolve all row dependencies at once before the rendering loop.
