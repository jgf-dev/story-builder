"""Database repository for the StoryBuilder Dashboard."""

import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Optional

from ..config import DB_PATH
from .models import ArchiveStats
from .models import Favorite
from .models import SearchResult
from .models import Story
from .models import StorySearchQuery
from .models import Tag


class DatabaseRepository:
    """Repository for database operations."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the repository with a database path."""
        self.db_path = db_path or DB_PATH
        self._ensure_db_exists()

    def _ensure_db_exists(self) -> None:
        """Ensure the database file exists."""
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """Get a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _row_to_story(self, row: sqlite3.Row, include_content: bool = False) -> Story:
        """Convert a database row to a Story object."""
        return Story(
            path=row["path"],
            title=row["title"],
            author=row["author"],
            publication_date=date.fromisoformat(row["publication_date"]) if row["publication_date"] else None,
            category=row["category"] or "",
            subcategory=row["subcategory"] or "",
            content=row["content"] if include_content else "",
            word_count=row["word_count"] or 0,
            year=row["year"] or 0,
            slug=row["slug"] or "",
            is_favorite=bool(row.get("is_favorite", 0)),
            tags=self._get_story_tags(row["path"]),
            snippet=row.get("snippet", ""),
        )

    def _get_story_tags(self, story_path: str) -> list[str]:
        """Get tags for a story."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT tag FROM story_tags WHERE story_path = ? ORDER BY tag",
                (story_path,)
            )
            return [row["tag"] for row in cursor.fetchall()]

    def search_stories(self, query: StorySearchQuery) -> SearchResult:
        """Search stories with filters and pagination."""
        with self._get_connection() as conn:
            # Build the WHERE clause
            where_conditions = []
            params = []

            # Full-text search
            if query.query:
                where_conditions.append("stories_fts MATCH ?")
                params.append(query.query)

            # Author filter
            if query.author:
                where_conditions.append("author LIKE ?")
                params.append(f"%{query.author}%")

            # Category filter
            if query.category:
                where_conditions.append("category = ?")
                params.append(query.category)

            # Date range filters
            if query.date_from:
                where_conditions.append("publication_date >= ?")
                params.append(query.date_from.isoformat())

            if query.date_to:
                where_conditions.append("publication_date <= ?")
                params.append(query.date_to.isoformat())

            # Favorites filter
            if query.favorites_only:
                where_conditions.append("EXISTS (SELECT 1 FROM favorites WHERE story_path = stories.path)")

            # Tags filter
            if query.tags:
                tag_placeholders = ",".join(["?"] * len(query.tags))
                where_conditions.append(
                    f"EXISTS (SELECT 1 FROM story_tags WHERE story_path = stories.path AND tag IN ({tag_placeholders}))"
                )
                params.extend(query.tags)

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # Count total results
            count_sql = f"""
                SELECT COUNT(*) as total
                FROM stories
                WHERE {where_clause}
            """
            total_count = conn.execute(count_sql, params).fetchone()["total"]

            # Build ORDER BY clause
            order_by = self._build_order_by(query.sort_by, query.sort_order)

            # Pagination
            offset = (query.page - 1) * query.page_size
            params.extend([query.page_size, offset])

            # Main query with snippet for FTS
            if query.query:
                select_clause = """
                    stories.*,
                    snippet(stories_fts, -1, '', '', '...', 32) as snippet,
                    EXISTS(SELECT 1 FROM favorites WHERE story_path = stories.path) as is_favorite
                """
                from_clause = "stories JOIN stories_fts ON stories.path = stories_fts.path"
            else:
                select_clause = """
                    stories.*,
                    '' as snippet,
                    EXISTS(SELECT 1 FROM favorites WHERE story_path = stories.path) as is_favorite
                """
                from_clause = "stories"

            sql = f"""
                SELECT {select_clause}
                FROM {from_clause}
                WHERE {where_clause}
                ORDER BY {order_by}
                LIMIT ? OFFSET ?
            """

            cursor = conn.execute(sql, params)
            stories = [self._row_to_story(row) for row in cursor.fetchall()]

            return SearchResult(
                stories=stories,
                total_count=total_count,
                page=query.page,
                page_size=query.page_size,
                query=query,
            )

    def _build_order_by(self, sort_by: str, sort_order: str) -> str:
        """Build ORDER BY clause."""
        order_map = {
            "relevance": "rank" if sort_order == "desc" else "rank DESC",
            "date": "publication_date",
            "title": "title",
            "author": "author",
            "word_count": "word_count",
        }
        column = order_map.get(sort_by, "publication_date")
        direction = "DESC" if sort_order == "desc" else "ASC"
        return f"{column} {direction}"

    def get_story(self, path: str, include_content: bool = True) -> Optional[Story]:
        """Get a single story by path."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM stories WHERE path = ?",
                (path,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_story(row, include_content)
            return None

    def get_story_by_slug(self, slug: str, include_content: bool = True) -> Optional[Story]:
        """Get a single story by slug."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM stories WHERE slug = ?",
                (slug,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_story(row, include_content)
            return None

    def list_stories(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "date",
        sort_order: str = "desc",
    ) -> SearchResult:
        """List all stories with pagination."""
        query = StorySearchQuery(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return self.search_stories(query)

    def get_categories(self) -> list[str]:
        """Get all unique categories."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT DISTINCT category FROM stories WHERE category IS NOT NULL AND category != '' ORDER BY category"
            )
            return [row["category"] for row in cursor.fetchall()]

    def get_authors(self) -> list[str]:
        """Get all unique authors."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT DISTINCT author FROM stories WHERE author IS NOT NULL AND author != '' ORDER BY author"
            )
            return [row["author"] for row in cursor.fetchall()]

    def get_all_tags(self) -> list[Tag]:
        """Get all tags with story counts."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT tag, COUNT(*) as story_count
                FROM story_tags
                GROUP BY tag
                ORDER BY story_count DESC, tag
            """)
            return [Tag(name=row["tag"], story_count=row["story_count"]) for row in cursor.fetchall()]

    def get_stats(self) -> ArchiveStats:
        """Get archive statistics."""
        with self._get_connection() as conn:
            stats = ArchiveStats()

            # Total stories
            stats.total_stories = conn.execute("SELECT COUNT(*) FROM stories").fetchone()[0]

            # Total authors
            stats.total_authors = conn.execute(
                "SELECT COUNT(DISTINCT author) FROM stories WHERE author IS NOT NULL AND author != ''"
            ).fetchone()[0]

            # Total categories
            stats.total_categories = conn.execute(
                "SELECT COUNT(DISTINCT category) FROM stories WHERE category IS NOT NULL AND category != ''"
            ).fetchone()[0]

            # Total words
            stats.total_words = conn.execute("SELECT COALESCE(SUM(word_count), 0) FROM stories").fetchone()[0]

            # Date range
            date_row = conn.execute(
                "SELECT MIN(publication_date), MAX(publication_date) FROM stories WHERE publication_date IS NOT NULL"
            ).fetchone()
            if date_row[0] and date_row[1]:
                stats.date_range = (date.fromisoformat(date_row[0]), date.fromisoformat(date_row[1]))

            # Stories by year
            cursor = conn.execute("""
                SELECT CAST(strftime('%Y', publication_date) AS INTEGER) as year, COUNT(*) as count
                FROM stories
                WHERE publication_date IS NOT NULL
                GROUP BY year
                ORDER BY year
            """)
            stats.stories_by_year = {row["year"]: row["count"] for row in cursor.fetchall()}

            # Stories by category
            cursor = conn.execute("""
                SELECT category, COUNT(*) as count
                FROM stories
                WHERE category IS NOT NULL AND category != ''
                GROUP BY category
                ORDER BY count DESC
            """)
            stats.stories_by_category = {row["category"]: row["count"] for row in cursor.fetchall()}

            # Top authors
            cursor = conn.execute("""
                SELECT author, COUNT(*) as count
                FROM stories
                WHERE author IS NOT NULL AND author != ''
                GROUP BY author
                ORDER BY count DESC
                LIMIT 20
            """)
            stats.stories_by_author = {row["author"]: row["count"] for row in cursor.fetchall()}

            # Average words per story
            if stats.total_stories > 0:
                stats.avg_words_per_story = stats.total_words / stats.total_stories

            # Favorites count
            stats.favorites_count = conn.execute("SELECT COUNT(*) FROM favorites").fetchone()[0]

            # Tagged stories count
            stats.tagged_stories_count = conn.execute(
                "SELECT COUNT(DISTINCT story_path) FROM story_tags"
            ).fetchone()[0]

            # Unique tags count
            stats.unique_tags_count = conn.execute("SELECT COUNT(DISTINCT tag) FROM story_tags").fetchone()[0]

            return stats

    # Favorites operations
    def get_favorites(self) -> list[Favorite]:
        """Get all favorites with story info."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT f.*, s.title, s.author, s.category
                FROM favorites f
                JOIN stories s ON f.story_path = s.path
                ORDER BY f.added_at DESC
            """)
            favorites = []
            for row in cursor.fetchall():
                fav = Favorite(
                    story_path=row["story_path"],
                    added_at=date.fromisoformat(row["added_at"]),
                    notes=row["notes"] or "",
                    tags=row["tags"].split(",") if row["tags"] else [],
                )
                favorites.append(fav)
            return favorites

    def add_favorite(self, story_path: str, notes: str = "", tags: list[str] = None) -> bool:
        """Add a story to favorites."""
        with self._get_connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO favorites (story_path, added_at, notes, tags) VALUES (?, ?, ?, ?)",
                    (story_path, date.today().isoformat(), notes, ",".join(tags or []))
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def remove_favorite(self, story_path: str) -> bool:
        """Remove a story from favorites."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM favorites WHERE story_path = ?",
                (story_path,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def is_favorite(self, story_path: str) -> bool:
        """Check if a story is favorited."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM favorites WHERE story_path = ?",
                (story_path,)
            )
            return cursor.fetchone() is not None

    def update_favorite(self, story_path: str, notes: str = None, tags: list[str] = None) -> bool:
        """Update favorite notes and tags."""
        with self._get_connection() as conn:
            updates = []
            params = []
            if notes is not None:
                updates.append("notes = ?")
                params.append(notes)
            if tags is not None:
                updates.append("tags = ?")
                params.append(",".join(tags))

            if not updates:
                return False

            params.append(story_path)
            sql = f"UPDATE favorites SET {', '.join(updates)} WHERE story_path = ?"
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor.rowcount > 0

    # Tag operations
    def add_tag(self, story_path: str, tag: str) -> bool:
        """Add a tag to a story."""
        with self._get_connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO story_tags (story_path, tag) VALUES (?, ?)",
                    (story_path, tag.lower().strip())
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def remove_tag(self, story_path: str, tag: str) -> bool:
        """Remove a tag from a story."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM story_tags WHERE story_path = ? AND tag = ?",
                (story_path, tag.lower().strip())
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_story_tags(self, story_path: str) -> list[str]:
        """Get all tags for a story."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT tag FROM story_tags WHERE story_path = ? ORDER BY tag",
                (story_path,)
            )
            return [row["tag"] for row in cursor.fetchall()]

    def search_by_tag(self, tag: str, page: int = 1, page_size: int = 20) -> SearchResult:
        """Search stories by tag."""
        query = StorySearchQuery(
            tags=[tag],
            page=page,
            page_size=page_size,
        )
        return self.search_stories(query)


# Singleton instance
_repository: Optional[DatabaseRepository] = None


def get_repository(db_path: Optional[str] = None) -> DatabaseRepository:
    """Get the singleton database repository instance."""
    global _repository
    if _repository is None or db_path is not None:
        _repository = DatabaseRepository(db_path)
    return _repository
