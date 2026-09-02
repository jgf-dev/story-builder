from _typeshed import Incomplete

import logging as std_logging
import os
import re
import sqlite3
import threading
from pathlib import Path
from typing import ClassVar
from sqlalchemy import Column, Integer, MetaData, Table, Text, func, literal_column
from sqlalchemy.engine import Engine
from sqlmodel import Field, Session, SQLModel, col, create_engine, select, text

logging: Logger


class Story(SQLModel, table=True):
    __tablename__: ClassVar[str] = "stories"
    id: int | None
    path: str
    orientation: str
    category: str | None
    story_slug: str | None
    chapter_num: int | None
    title: str | None
    author_name: str | None
    author_email: str | None
    publication_date: str | None
    url: str | None
    char_count: int
    word_count: int
    content: str
    created_at: str | None

    def __init__(self, *, id: Decimal | bool | bytes | float | int | str | None = ..., path: bytearray | bytes | str = ..., orientation: bytearray | bytes | str = ..., category: bytearray | bytes | str | None = ..., story_slug: bytearray | bytes | str | None = ..., chapter_num: Decimal | bool | bytes | float | int | str | None = ..., title: bytearray | bytes | str | None = ..., author_name: bytearray | bytes | str | None = ..., author_email: bytearray | bytes | str | None = ..., publication_date: bytearray | bytes | str | None = ..., url: bytearray | bytes | str | None = ..., char_count: Decimal | bool | bytes | float | int | str = ..., word_count: Decimal | bool | bytes | float | int | str = ..., content: bytearray | bytes | str = ..., created_at: bytearray | bytes | str | None = ..., **kwargs: Incomplete) -> None: ...


metadata_fts: MetaData
stories_fts: Table
STORY_COLUMNS: tuple[Literal['id'], Literal['path'], Literal['orientation'], Literal['category'], Literal['story_slug'], Literal['chapter_num'], Literal['title'], Literal['author_name'], Literal['author_email'], Literal['publication_date'], Literal['url'], Literal['char_count'], Literal['word_count'], Literal['content'], Literal['created_at']]
SCHEMA: Literal['\nCREATE TABLE IF NOT EXISTS stories (\n    id              INTEGER PRIMARY KEY AUTOINCREMENT,\n    path            TEXT UNIQUE NOT NULL,\n    orientation     TEXT NOT NULL DEFAULT \'gay\',\n    category        TEXT,\n    story_slug      TEXT,\n    chapter_num     INTEGER,\n    title           TEXT,\n    author_name     TEXT,\n    author_email    TEXT,\n    publication_date TEXT,\n    url             TEXT,\n    char_count      INTEGER NOT NULL,\n    word_count      INTEGER NOT NULL,\n    content         TEXT NOT NULL,\n    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP\n);\n\nCREATE VIRTUAL TABLE IF NOT EXISTS stories_fts USING fts5(\n    title,\n    author_name,\n    content,\n    content=\'stories\',\n    content_rowid=\'id\'\n);\n\nCREATE TRIGGER IF NOT EXISTS stories_ai AFTER INSERT ON stories BEGIN\n    INSERT INTO stories_fts(rowid, title, author_name, content)\n    VALUES (new.id, new.title, new.author_name, new.content);\nEND;\n\nCREATE TRIGGER IF NOT EXISTS stories_ad AFTER DELETE ON stories BEGIN\n    INSERT INTO stories_fts(stories_fts, rowid, title, author_name, content)\n    VALUES (\'delete\', old.id, old.title, old.author_name, old.content);\nEND;\n\nCREATE TRIGGER IF NOT EXISTS stories_au AFTER UPDATE ON stories BEGIN\n    INSERT INTO stories_fts(stories_fts, rowid, title, author_name, content)\n    VALUES (\'delete\', old.id, old.title, old.author_name, old.content);\n    INSERT INTO stories_fts(rowid, title, author_name, content)\n    VALUES (new.id, new.title, new.author_name, new.content);\nEND;\n'] = """
CREATE TABLE IF NOT EXISTS stories (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    path            TEXT UNIQUE NOT NULL,
    orientation     TEXT NOT NULL DEFAULT 'gay',
    category        TEXT,
    story_slug      TEXT,
    chapter_num     INTEGER,
    title           TEXT,
    author_name     TEXT,
    author_email    TEXT,
    publication_date TEXT,
    url             TEXT,
    char_count      INTEGER NOT NULL,
    word_count      INTEGER NOT NULL,
    content         TEXT NOT NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE VIRTUAL TABLE IF NOT EXISTS stories_fts USING fts5(
    title,
    author_name,
    content,
    content='stories',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS stories_ai AFTER INSERT ON stories BEGIN
    INSERT INTO stories_fts(rowid, title, author_name, content)
    VALUES (new.id, new.title, new.author_name, new.content);
END;

CREATE TRIGGER IF NOT EXISTS stories_ad AFTER DELETE ON stories BEGIN
    INSERT INTO stories_fts(stories_fts, rowid, title, author_name, content)
    VALUES ('delete', old.id, old.title, old.author_name, old.content);
END;

CREATE TRIGGER IF NOT EXISTS stories_au AFTER UPDATE ON stories BEGIN
    INSERT INTO stories_fts(stories_fts, rowid, title, author_name, content)
    VALUES ('delete', old.id, old.title, old.author_name, old.content);
    INSERT INTO stories_fts(rowid, title, author_name, content)
    VALUES (new.id, new.title, new.author_name, new.content);
END;
"""
INDEXES: Literal['\nCREATE INDEX IF NOT EXISTS idx_stories_category       ON stories(category);\nCREATE INDEX IF NOT EXISTS idx_stories_story_slug      ON stories(story_slug);\nCREATE INDEX IF NOT EXISTS idx_stories_author_name     ON stories(author_name);\nCREATE INDEX IF NOT EXISTS idx_stories_publication_date ON stories(publication_date);\nCREATE INDEX IF NOT EXISTS idx_stories_char_count      ON stories(char_count);\n'] = """
CREATE INDEX IF NOT EXISTS idx_stories_category       ON stories(category);
CREATE INDEX IF NOT EXISTS idx_stories_story_slug      ON stories(story_slug);
CREATE INDEX IF NOT EXISTS idx_stories_author_name     ON stories(author_name);
CREATE INDEX IF NOT EXISTS idx_stories_publication_date ON stories(publication_date);
CREATE INDEX IF NOT EXISTS idx_stories_char_count      ON stories(char_count);
"""


def migrate_legacy_schema(conn: sqlite3.Connection) -> bool: ...


def init_db(db_path: str) -> "sqlite3.Connection": ...


def get_conn() -> "sqlite3.Connection | None": ...


def execute_query(sql: str, params: tuple = ()) -> list[dict]: ...


def search_stories(fts_query: str = "", category: "str | None" = None, author: "str | None" = None, date_from: "str | None" = None, date_to: "str | None" = None, **kwargs: Incomplete) -> list[dict]: ...


def insert_story(*, output_path: str, title: str, author: str, story_date: str, url: str, content: str) -> bool: ...


def story_exists(output_path: str, story_date: str = "") -> bool: ...


def get_story(output_path: str, story_date: str = "") -> "dict | None": ...


def optimize_fts() -> None: ...


def close_db() -> None: ...
