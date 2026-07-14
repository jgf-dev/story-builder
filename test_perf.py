import time
from scripts.dashboard.data.repository import get_repository
from scripts.dashboard.data.models import StorySearchQuery
import sqlite3
import os

def run_test():
    db_path = "test_db.sqlite3"

    # Create some dummy data
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE IF NOT EXISTS stories (path TEXT, title TEXT, author TEXT, publication_date TEXT, category TEXT, subcategory TEXT, content TEXT, word_count INTEGER, year INTEGER, slug TEXT)")
    conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS stories_fts USING fts5(path, content, title, author)")
    conn.execute("CREATE TABLE IF NOT EXISTS story_tags (story_path TEXT, tag TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS favorites (story_path TEXT, added_at TEXT, notes TEXT, tags TEXT)")

    conn.execute("DELETE FROM stories")
    conn.execute("DELETE FROM story_tags")
    for i in range(100):
        path = f"path_{i}"
        conn.execute("INSERT INTO stories (path, title, author, publication_date) VALUES (?, ?, ?, ?)", (path, f"Title {i}", "Author", "2023-01-01"))
        for j in range(5):
            conn.execute("INSERT INTO story_tags (story_path, tag) VALUES (?, ?)", (path, f"tag_{j}"))
    conn.commit()
    conn.close()

    repo = get_repository(db_path)

    t0 = time.time()
    for _ in range(50):
        query = StorySearchQuery(page=1, page_size=50, sort_by="date")
        repo.search_stories(query)
    t1 = time.time()
    print(f"Time taken: {t1 - t0:.4f} seconds")

    os.remove(db_path)

run_test()
