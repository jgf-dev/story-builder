-- Step 1: Create the target table with explicit TEXT type for content
CREATE TABLE stories (
    id               INTEGER,
    category         TEXT,
    story_slug       TEXT,
    chapter_num      INTEGER,
    title            TEXT,
    author_name      TEXT,
    author_email     TEXT,
    publication_date TEXT,
    char_count       INTEGER,
    word_count       INTEGER,
    content          TEXT  -- No length limit in SQLite
);

