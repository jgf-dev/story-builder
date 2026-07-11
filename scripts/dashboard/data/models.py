"""Data models for the StoryBuilder Dashboard."""

from dataclasses import dataclass
from dataclasses import field
from datetime import date


@dataclass
class StorySearchQuery:
    """Query parameters for story search."""

    query: str = ""
    author: str = ""
    category: str = ""
    date_from: date | None = None
    date_to: date | None = None
    tags: list[str] = field(default_factory=list)
    favorites_only: bool = False
    page: int = 1
    page_size: int = 20
    sort_by: str = "relevance"  # relevance, date, title, author
    sort_order: str = "desc"  # asc, desc


@dataclass
class Story:
    """Represents a story from the archive."""

    path: str
    title: str
    author: str
    publication_date: date | None = None
    category: str = ""
    subcategory: str = ""
    content: str = ""
    word_count: int = 0
    year: int = 0
    slug: str = ""
    is_favorite: bool = False
    tags: list[str] = field(default_factory=list)
    snippet: str = ""

    @property
    def display_date(self) -> str:
        """Format publication date for display."""
        if self.publication_date:
            return self.publication_date.strftime("%B %d, %Y")
        return "Unknown date"

    @property
    def short_path(self) -> str:
        """Get a shortened path for display."""
        parts = self.path.split("/")
        if len(parts) > 2:
            return "/".join(parts[-2:])
        return self.path


@dataclass
class Favorite:
    """Represents a user favorite."""

    story_path: str
    added_at: date
    notes: str = ""
    tags: list[str] = field(default_factory=list)

    @property
    def display_date(self) -> str:
        """Format added date for display."""
        return self.added_at.strftime("%B %d, %Y")


@dataclass
class Tag:
    """Represents a tag."""

    name: str
    color: str = "#6c757d"
    description: str = ""
    story_count: int = 0

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, Tag):
            return self.name == other.name
        return self.name == other


@dataclass
class SearchResult:
    """Container for search results with pagination info."""

    stories: list[Story]
    total_count: int
    page: int
    page_size: int
    query: StorySearchQuery

    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        if self.page_size <= 0:
            return 0
        return (self.total_count + self.page_size - 1) // self.page_size

    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1

    @property
    def start_index(self) -> int:
        """Get 1-based start index of current page."""
        return (self.page - 1) * self.page_size + 1

    @property
    def end_index(self) -> int:
        """Get 1-based end index of current page."""
        return min(self.page * self.page_size, self.total_count)


@dataclass
class ArchiveStats:
    """Statistics about the story archive."""

    total_stories: int = 0
    total_authors: int = 0
    total_categories: int = 0
    total_words: int = 0
    date_range: tuple[date | None, date | None] = (None, None)
    stories_by_year: dict[int, int] = field(default_factory=dict)
    stories_by_category: dict[str, int] = field(default_factory=dict)
    stories_by_author: dict[str, int] = field(default_factory=dict)
    avg_words_per_story: float = 0.0
    favorites_count: int = 0
    tagged_stories_count: int = 0
    unique_tags_count: int = 0
