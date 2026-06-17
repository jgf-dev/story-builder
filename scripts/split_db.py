#!/usr/bin/env python3
"""Split pre2020.db and 2020plus.db into 5-year bucketed partition databases."""
import sqlite3
import os
import time

schema_sql = '''
CREATE TABLE IF NOT EXISTS stories (
    id              INTEGER PRIMARY KEY,
    path            TEXT UNIQUE NOT NULL,
    orientation     TEXT NOT NULL DEFAULT 'gay',
    category        TEXT NOT NULL,
    story_slug      TEXT NOT NULL,
    chapter_num     INTEGER,
    title           TEXT NOT NULL,
    author_name     TEXT,
    author_email    TEXT,
    publication_date TEXT,
    url             TEXT,
    email_date      TEXT,
    char_count      INTEGER NOT NULL,
    word_count      INTEGER NOT NULL,
    content         TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_stories_category       ON stories(category);
CREATE INDEX IF NOT EXISTS idx_stories_story_slug      ON stories(story_slug);
CREATE INDEX IF NOT EXISTS idx_stories_author_name     ON stories(author_name);
CREATE INDEX IF NOT EXISTS idx_stories_publication_date ON stories(publication_date);
CREATE INDEX IF NOT EXISTS idx_stories_char_count      ON stories(char_count);
'''

# We will read from pre2020.db and 2020plus.db in stories/db
src_pre2020 = os.path.abspath('stories/db/pre2020.db')
src_2020plus = os.path.abspath('stories/db/2020plus.db')

os.makedirs('stories/db', exist_ok=True)

# Define partition targets
partitions = [
    ('pre2000', "publication_date < '2000-01-01'"),
    ('2000to2001', "publication_date >= '2000-01-01' AND publication_date < '2002-01-01'"),
    ('2002to2003', "publication_date >= '2002-01-01' AND publication_date < '2004-01-01'"),
    ('2004', "publication_date >= '2004-01-01' AND publication_date < '2005-01-01'"),
    ('2005to2009', "publication_date >= '2005-01-01' AND publication_date < '2010-01-01'"),
    ('2010to2014', "publication_date >= '2010-01-01' AND publication_date < '2015-01-01'"),
    ('2015to2019', "publication_date >= '2015-01-01' AND publication_date < '2020-01-01'"),
    ('2020to2024', "publication_date >= '2020-01-01' AND publication_date < '2025-01-01'"),
    ('2025', "publication_date >= '2025-01-01' AND publication_date < '2026-01-01'"),
    ('2026plus', "publication_date >= '2026-01-01'"),
]

cols = "path, orientation, category, story_slug, chapter_num, title, author_name, author_email, publication_date, url, email_date, char_count, word_count, content"

for label, where in partitions:
    dst = f'stories/db/{label}.db'
    if os.path.exists(dst):
        os.remove(dst)
        
    db = sqlite3.connect(dst)
    db.executescript(schema_sql)
    db.commit()
    db.execute('PRAGMA journal_mode=OFF')
    db.execute('PRAGMA synchronous=OFF')
    
    t0 = time.time()
    
    # 1. Attach and copy from pre2020.db
    if os.path.exists(src_pre2020):
        db.execute(f"ATTACH '{src_pre2020}' AS src_pre")
        db.execute(f"INSERT OR IGNORE INTO stories ({cols}) SELECT {cols} FROM src_pre.stories WHERE {where}")
        db.commit()
        db.execute("DETACH src_pre")
        db.commit()
        
    # 2. Attach and copy from 2020plus.db (for 2020to2024, 2025, and 2026plus)
    if os.path.exists(src_2020plus) and label in ('2020to2024', '2025', '2026plus'):
        db.execute(f"ATTACH '{src_2020plus}' AS src_plus")
        db.execute(f"INSERT OR IGNORE INTO stories ({cols}) SELECT {cols} FROM src_plus.stories WHERE {where}")
        db.commit()
        db.execute("DETACH src_plus")
        db.commit()
        
    # Build FTS5 index
    db.execute('''CREATE VIRTUAL TABLE stories_fts USING fts5(
        title, author_name, content, content=stories, content_rowid=id)''')
    db.execute("INSERT INTO stories_fts(stories_fts) VALUES ('rebuild')")
    db.execute("INSERT INTO stories_fts(stories_fts) VALUES ('optimize')")
    db.commit()
    
    cnt = db.execute('SELECT COUNT(*) FROM stories').fetchone()[0]
    elapsed = time.time() - t0
    size = os.path.getsize(dst) / (1024*1024)
    print(f'{label}: {cnt:,} stories, {size:.1f} MB ({elapsed:.1f}s)')
    db.close()

print('Done splitting databases.')
