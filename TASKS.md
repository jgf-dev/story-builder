1. Partial FTS Optimization: In partitioned mode, calling optimize_fts() only optimizes active connections currently loaded in_connections. Partitions that haven't been written to during the current run are ignored.
Recommendation: Implement a mechanism to scan the partition folder and run the optimize PRAGMA command on all year databases in batch mode.
2. Lack of cross-partition searching: While partitioning keeps file sizes highly manageable, SQLite cannot natively query across multiple closed databases.
Recommendation: If using partitioned databases, ensure search clients (such as story_db.py) dynamically attach partition files using ATTACH DATABASE statements when performing global queries.
