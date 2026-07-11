"""Configuration constants for the StoryBuilder Dashboard."""

from pathlib import Path


# Base paths
BASE_DIR = Path(__file__).parent.parent.parent.parent
STORIES_DIR = BASE_DIR / "stories"
DB_DIR = STORIES_DIR / "db"

# Database configuration for partitioned databases (by year)
DB_CONFIG = {
    "base_path": DB_DIR,
    "pattern": "stories_{year}.db",
    "meta_db": DB_DIR / "meta.db",
    "min_year": 1990,
    "max_year": 2025,
}

# Pagination settings
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Search settings
DEFAULT_SNIPPET_LENGTH = 200
MAX_SNIPPET_LENGTH = 500

# UI settings
PAGE_TITLE = "StoryBuilder Archive"
PAGE_ICON = "📚"
LAYOUT = "wide"

# CSS Styles
CSS_STYLES = """
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* Story card styling */
    .story-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #dee2e6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .story-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .story-card.favorite {
        border-left: 4px solid #ffc107;
        background: linear-gradient(135deg, #fff8e1 0%, #fff3c4 100%);
    }

    /* Story metadata */
    .story-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #212529;
        margin-bottom: 0.5rem;
    }
    .story-meta {
        font-size: 0.85rem;
        color: #6c757d;
        margin-bottom: 0.5rem;
    }
    .story-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
        margin-top: 0.5rem;
    }
    .tag {
        background: #e9ecef;
        color: #495057;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .tag.favorite {
        background: #ffc107;
        color: #212529;
    }

    /* Search result snippet */
    .search-snippet {
        background: #f8f9fa;
        border-left: 3px solid #0d6efd;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
        font-size: 0.9rem;
        line-height: 1.5;
        color: #343a40;
    }
    .search-snippet mark {
        background: #fff3cd;
        padding: 0 0.2rem;
        border-radius: 2px;
    }

    /* Story reader */
    .story-reader {
        background: #ffffff;
        border-radius: 12px;
        padding: 2.5rem;
        border: 1px solid #dee2e6;
        line-height: 1.8;
        font-size: 1.05rem;
        color: #212529;
    }
    .story-reader h1, .story-reader h2, .story-reader h3 {
        color: #212529;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .story-reader p {
        margin-bottom: 1.25rem;
        text-align: justify;
    }

    /* Stats cards */
    .stat-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #dee2e6;
        text-align: center;
        transition: transform 0.2s ease;
    }
    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .stat-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #0d6efd;
        line-height: 1;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #6c757d;
        margin-top: 0.5rem;
        font-weight: 500;
    }

    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: #f8f9fa;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0d6efd 0%, #0b5ed7 100%);
        border: none;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #0b5ed7 0%, #0a58ca 100%);
        box-shadow: 0 2px 8px rgba(13, 110, 253, 0.3);
    }

    /* Tag input styling */
    .tag-input-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        padding: 0.5rem;
        background: #f8f9fa;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }

    /* Pagination */
    .pagination-container {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 1rem;
        margin-top: 2rem;
    }

    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #0d6efd 0%, #6ea8fe 100%);
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #212529;
    }

    /* Metric styling */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border: 1px solid #dee2e6;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    /* Selectbox styling */
    .stSelectbox > div > div {
        border-radius: 8px;
    }

    /* Text input styling */
    .stTextInput > div > div > input {
        border-radius: 8px;
    }

    /* Text area styling */
    .stTextArea > div > div > textarea {
        border-radius: 8px;
    }

    /* Dataframe styling */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #a1a1a1;
    }

    /* Alert styling */
    .stAlert {
        border-radius: 8px;
        border: none;
    }

    /* Footer */
    .dashboard-footer {
        text-align: center;
        padding: 2rem;
        color: #6c757d;
        font-size: 0.85rem;
        border-top: 1px solid #dee2e6;
        margin-top: 3rem;
    }
</style>
"""

# Page configuration
PAGES = {
    "search": "🔍 Search & Explore",
    "read": "📖 Read Story",
    "favorites": "⭐ Favorites & Tags",
    "stats": "📊 Archive Stats",
}

# Default search filters
DEFAULT_FILTERS = {
    "author": "",
    "category": "",
    "date_from": None,
    "date_to": None,
    "tags": [],
    "favorites_only": False,
}

# Chart color palette
CHART_COLORS = [
    "#0d6efd",
    "#6ea8fe",
    "#198754",
    "#20c997",
    "#ffc107",
    "#fd7e14",
    "#dc3545",
    "#6f42c1",
    "#d63384",
    "#0dcaf0",
    "#6c757d",
    "#343a40",
]
