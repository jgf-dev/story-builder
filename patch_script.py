
with open("src/storybuilder/downloader/db.py", "r") as f:
    content = f.read()

# Make sure concurrent.futures is imported
if "import concurrent.futures" not in content:
    # Add it at the top where imports usually are.
    content = "import concurrent.futures\n" + content


old_func = """def optimize_fts() -> None:
    \"\"\"Rebuild the FTS index for optimal search performance.\"\"\"
    with _lock:
        conns = list(_connections.values())
        if _conn is not None and not _is_partitioned:
            conns.append(_conn)

        for conn in conns:
            try:
                conn.execute("INSERT INTO stories_fts(stories_fts) VALUES ('optimize')")
                conn.commit()
            except sqlite3.OperationalError:
                pass"""

new_func = """def optimize_fts() -> None:
    \"\"\"Rebuild the FTS index for optimal search performance.\"\"\"
    with _lock:
        conns = list(_connections.values())
        if _conn is not None and not _is_partitioned:
            conns.append(_conn)

    def _opt(conn: sqlite3.Connection) -> None:
        try:
            conn.execute("INSERT INTO stories_fts(stories_fts) VALUES ('optimize')")
            conn.commit()
        except sqlite3.OperationalError:
            pass

    if conns:
        # SQLite FTS optimize can be CPU/IO intensive.
        # Using a ThreadPoolExecutor prevents holding the global _lock
        # and blocking other inserts during long optimize operations.
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(conns), 10)) as executor:
            list(executor.map(_opt, conns))"""

content = content.replace(old_func, new_func)

with open("src/storybuilder/downloader/db.py", "w") as f:
    f.write(content)
