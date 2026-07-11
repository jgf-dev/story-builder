#!/usr/bin/env python3
"""
Query the stories SQLite database — search, browse, and export.

Usage:
    # Full-text search
    python scripts/story_db.py search "vampire"
    python scripts/story_db.py search "werewolf" --author "Mark Arsenault"
    python scripts/story_db.py search "adventure" --category college --limit 20
    python scripts/story_db.py search "romance" --date-from 2023-01-01

    # Get a specific story by path/slug
    python scripts/story_db.py get "721-anderson-avenue"
    python scripts/story_db.py get "a-beautiful-friendship" --export

    # Browse stories
    python scripts/story_db.py list --category adult-friends --limit 10
    python scripts/story_db.py list --author "Mark Arsenault" --sort date

    # Stats
    python scripts/story_db.py stats
    python scripts/story_db.py stats --category college
"""

import argparse
import os
import sqlite3
import sys
from pathlib import Path


def connect(db_path: str) -> sqlite3.Connection:
    if not Path(db_path).exists():
        print(
            f"Error: Database '{db_path}' not found. Run import_to_sqlite.py first.",
            file=sys.stderr,
        )
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _resolve_connection(args) -> "tuple[sqlite3.Connection, list[str] | None]":
    """Resolve connection from args, supporting both --db and --db-dir.

    Returns (conn, db_paths) where db_paths is always None (monolithic mode).
    Auto-detects if --db is a directory and resolves it to stories.db.
    """
    db_path = getattr(args, "db_dir", None) or args.db
    if Path(db_path).is_dir():
        resolved_path = os.path.join(db_path, "stories.db")
    else:
        resolved_path = db_path

    conn = connect(resolved_path)
    return conn, None


# ——— Search ————————————————————————————————————————————————————————————————————


def cmd_search(conn: sqlite3.Connection, args, db_paths: "list[str] | None" = None):
    """Full-text search across titles, authors, and content."""
    conditions = ["stories_fts MATCH ?"]
    params = [args.query]

    if args.author:
        conditions.append("s.author_name LIKE ?")
        params.append(f"%{args.author}%")
    if args.category:
        conditions.append("s.category = ?")
        params.append(args.category)
    if args.date_from:
        conditions.append("s.publication_date >= ?")
        params.append(args.date_from)
    if args.date_to:
        conditions.append("s.publication_date <= ?")
        params.append(args.date_to)

    where = " AND ".join(conditions)

    sql = f"""
        SELECT s.id, s.path, s.category, s.story_slug, s.chapter_num,
               s.title, s.author_name, s.publication_date,
               s.char_count, s.word_count,
               snippet(stories_fts, 2, '<b>', '</b>', '…', 40) AS snippet
        FROM stories s
        JOIN stories_fts ON s.id = stories_fts.rowid
        WHERE {where}
        ORDER BY rank
        LIMIT ?
    """
    params.append(args.limit)
    rows = conn.execute(sql, params).fetchall()

    if not rows:
        print(f"No results for '{args.query}'")
        return

    print(f"Found {len(rows)} result(s) for '{args.query}':\n")
    for row in rows:
        print(f"  [{row['id']}] {row['title']}")
        print(f"       Author:  {row['author_name'] or 'Unknown'}")
        print(f"       Date:    {row['publication_date'] or 'Unknown'}")
        print(f"       Category: {row['category']}  |  {row['word_count']:,} words")
        print(f"       Path:    {row['path']}")
        if args.snippets:
            snip = row["snippet"] or "(no snippet)"
            print(f"       Snippet: {snip}")
        print()


# ——— Get ————————————————————————————————————————————————————————————————————————


def cmd_get(conn: sqlite3.Connection, args, db_paths: "list[str] | None" = None):
    """Retrieve a specific story or all chapters of a story."""
    slug = args.slug

    sql = "SELECT * FROM stories WHERE path = ? OR story_slug = ?"
    rows = conn.execute(sql, (slug, slug)).fetchall()

    if not rows:
        print(f"No story found for '{slug}'")
        return

    if args.export:
        # Export to files
        out_dir = Path(args.export_dir) / rows[0]["story_slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        for row in rows:
            fname = Path(row["path"]).name
            out_path = out_dir / fname
            with Path(out_path).open("w", encoding="utf-8") as f:
                f.write(f"{'=' * 80}\n")
                f.write(f"Title: {row['title']}\n")
                f.write(f"Author: {row['author_name']}")
                if row["author_email"]:
                    f.write(f" <{row['author_email']}>")
                f.write(f"\nPublication Date: {row['publication_date']}\n")
                f.write(f"URL: {row['url']}\n")
                f.write(f"{'=' * 80}\n\n")
                f.write(row["content"])
            print(f"  Exported: {out_path}")
        print(f"Exported {len(rows)} chapter(s) to {out_dir}/")
        return

    # Display
    for row in rows:
        print(f"\n{'=' * 70}")
        print(f"Title:    {row['title']}")
        print(
            f"Author:   {row['author_name'] or 'Unknown'}"
            + (f" <{row['author_email']}>" if row["author_email"] else ""),
        )
        print(f"Date:     {row['publication_date'] or 'Unknown'}")
        print(f"URL:      {row['url'] or 'N/A'}")
        print(f"Category: {row['category']}")
        print(f"Chapter:  {row['chapter_num'] or 'single'}")
        print(f"Size:     {row['char_count']:,} chars / {row['word_count']:,} words")
        print(f"{'=' * 70}")

        if not args.no_content:
            content = row["content"]
            if args.max_chars and len(content) > args.max_chars:
                content = content[: args.max_chars] + f"\n\n… (truncated, {row['char_count']:,} total chars)"
            print(content)


# ——— List ———————————————————————————————————————————————————————————————————————


def cmd_list(conn: sqlite3.Connection, args, db_paths: "list[str] | None" = None):
    """Browse stories with filters."""
    conditions = ["1=1"]
    params = []

    if args.category:
        conditions.append("category = ?")
        params.append(args.category)
    if args.author:
        conditions.append("author_name LIKE ?")
        params.append(f"%{args.author}%")
    if args.date_from:
        conditions.append("publication_date >= ?")
        params.append(args.date_from)
    if args.story_slug:
        conditions.append("story_slug = ?")
        params.append(args.story_slug)

    order = {
        "date": "publication_date DESC",
        "title": "title ASC",
        "words": "word_count DESC",
        "chars": "char_count DESC",
    }.get(args.sort, "publication_date DESC")

    sql = f"""
        SELECT id, path, category, story_slug, title, author_name,
               publication_date, char_count, word_count
        FROM stories
        WHERE {" AND ".join(conditions)}
        ORDER BY {order}
        LIMIT ?
    """
    params.append(args.limit)
    rows = conn.execute(sql, params).fetchall()

    if not rows:
        print("No stories found.")
        return

    # Column widths
    print(
        f"{'ID':>6}  {'Title':<45}  {'Author':<25}  {'Date':>10}  {'Words':>8}  Category",
    )
    print("-" * 120)
    for row in rows:
        title = row["title"][:44] if row["title"] else ""
        author = (row["author_name"] or "")[:24]
        print(
            f"{row['id']:>6}  {title:<45}  {author:<25}  {row['publication_date'] or '':>10}  {row['word_count']:>8,}  {row['category']}",
        )


# ——— Stats ——————————————————————————————————————————————————————————————————————


def cmd_stats(conn: sqlite3.Connection, args, db_paths: "list[str] | None" = None):
    """Show database statistics."""
    where = ""
    params = []
    if args.category:
        where = "WHERE category = ?"
        params.append(args.category)

    total = conn.execute(f"SELECT COUNT(*) FROM stories {where}", params).fetchone()[0]
    total_chars = conn.execute(f"SELECT SUM(char_count) FROM stories {where}", params).fetchone()[0] or 0
    total_words = conn.execute(f"SELECT SUM(word_count) FROM stories {where}", params).fetchone()[0] or 0

    print(
        f"\n=== Database Stats{' for ' + args.category if args.category else ''} ===\n",
    )
    print(f"  Stories:     {total:,}")
    print(f"  Total chars: {total_chars:,}")
    print(f"  Total words: {total_words:,}")
    if total > 0:
        print(f"  Avg chars:   {total_chars // total:,}")
        print(f"  Avg words:   {total_words // total:,}")

    # Top categories
    print("\n  Top categories:")
    cats = conn.execute(
        f"""
        SELECT category, COUNT(*) as cnt
        FROM stories {where or "WHERE 1=1"}
        GROUP BY category ORDER BY cnt DESC LIMIT 15
        """,
        params if where else [],
    ).fetchall()
    for c in cats:
        print(f"    {c['category']:<25} {c['cnt']:>6,}")

    # Top authors
    print("\n  Top authors:")
    authors = conn.execute(
        f"""
        SELECT author_name, COUNT(*) as cnt, SUM(word_count) as total_words
        FROM stories {where or "WHERE 1=1"}
        GROUP BY author_name ORDER BY cnt DESC LIMIT 15
        """,
        params if where else [],
    ).fetchall()
    for a in authors:
        name = (a["author_name"] or "Unknown")[:30]
        print(f"    {name:<30} {a['cnt']:>5} stories  ({a['total_words']:,} words)")

    # Date range
    daterange = conn.execute(
        f"""SELECT MIN(publication_date), MAX(publication_date)
        FROM stories {where}""",
        params,
    ).fetchone()
    d_min = daterange[0]
    d_max = daterange[1]
    print(f"\n  Date range:  {d_min} — {d_max}")

    print()


# ——— Main ————————————————————————————————————————————————————————————————————————


def main():
    parser = argparse.ArgumentParser(description="Query the stories SQLite database")
    parser.add_argument(
        "--db",
        default="stories/db",
        help="Database directory or file. Searches all .db files if a directory.",
    )
    parser.add_argument(
        "--db-dir",
        default=None,
        help="Directory with split .db files (overrides --db)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # search
    p = sub.add_parser("search", help="Full-text search")
    p.add_argument("query", help="Search query (FTS5 syntax)")
    p.add_argument("--author", help="Filter by author name")
    p.add_argument("--category", help="Filter by category")
    p.add_argument("--date-from", help="Earliest publication date (YYYY-MM-DD)")
    p.add_argument("--date-to", help="Latest publication date (YYYY-MM-DD)")
    p.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")
    p.add_argument(
        "--snippets",
        action="store_true",
        default=True,
        help="Show content snippets (default: yes)",
    )
    p.add_argument(
        "--no-snippets",
        dest="snippets",
        action="store_false",
        help="Hide content snippets",
    )

    # get
    p = sub.add_parser("get", help="Retrieve a story by path or slug")
    p.add_argument("slug", help="Story path or slug")
    p.add_argument("--export", action="store_true", help="Export to .txt files")
    p.add_argument(
        "--export-dir",
        default="exported_stories",
        help="Export directory (default: exported_stories/)",
    )
    p.add_argument(
        "--no-content",
        action="store_true",
        help="Show metadata only, not story text",
    )
    p.add_argument(
        "--max-chars",
        type=int,
        default=5000,
        help="Max chars to display (default: 5000)",
    )

    # list
    p = sub.add_parser("list", help="Browse stories")
    p.add_argument("--category", help="Filter by category")
    p.add_argument("--author", help="Filter by author")
    p.add_argument("--story-slug", help="Filter by story slug")
    p.add_argument("--date-from", help="Earliest date (YYYY-MM-DD)")
    p.add_argument(
        "--sort",
        choices=["date", "title", "words", "chars"],
        default="date",
        help="Sort order (default: date)",
    )
    p.add_argument("--limit", type=int, default=30, help="Max results (default: 30)")

    # stats
    p = sub.add_parser("stats", help="Database statistics")
    p.add_argument("--category", help="Filter by category")

    args = parser.parse_args()
    conn, db_paths = _resolve_connection(args)

    dispatch = {
        "search": cmd_search,
        "get": cmd_get,
        "list": cmd_list,
        "stats": cmd_stats,
    }
    dispatch[args.command](conn, args, db_paths)
    conn.close()


if __name__ == "__main__":
    main()
