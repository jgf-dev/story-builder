import streamlit as st
import sqlite3
import os
import glob
import pandas as pd
import plotly.express as px
from pathlib import Path

# Define paths
DB_DIR = "stories/db"
NLP_DB_PATH = "nlp_analysis.db"
META_DB_PATH = "stories/db/dashboard_metadata.db"

# Set up page config
st.set_page_config(
    page_title="StoryBuilder Workspace Dashboard",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS for premium design
st.markdown(
    """
    <style>
        /* Main background and container styling */
        .reportview-container {
            background: #0b1020;
        }

        /* Heading styles */
        h1, h2, h3 {
            font-family: 'Outfit', 'Inter', sans-serif;
            font-weight: 700;
            color: #e8eefc;
        }

        /* Card styling */
        .story-card {
            background-color: rgba(22, 34, 64, 0.6);
            border: 1px solid rgba(148, 163, 184, 0.15);
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 12px;
            transition: all 0.2s ease-in-out;
        }
        .story-card:hover {
            border-color: rgba(125, 211, 252, 0.4);
            transform: translateY(-2px);
            background-color: rgba(22, 34, 64, 0.85);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        }

        /* Snippet highlight styling */
        .highlight {
            background-color: rgba(251, 191, 36, 0.25);
            color: #fbbf24;
            padding: 2px 4px;
            border-radius: 4px;
            font-weight: bold;
        }

        /* Sidebar styling custom overrides */
        .css-1d391kg {
            background-color: #09101f;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------------------
# DATABASE & DATA LOADING ENGINE
# ------------------------------------------------------------------------------


def get_db_files():
    """Retrieve all year-partitioned databases, sorted."""
    if not os.path.exists(DB_DIR):
        return []
    db_files = sorted(glob.glob(os.path.join(DB_DIR, "[0-9][0-9][0-9][0-9].db")))
    return db_files


def get_meta_conn():
    """Establish connection to local dashboard metadata (favorites & tags)."""
    os.makedirs(os.path.dirname(META_DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(META_DB_PATH, check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_path TEXT UNIQUE,
            title TEXT,
            author TEXT,
            tags TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    return conn


@st.cache_resource
def get_nlp_conn():
    """Establish cached connection to NLP database."""
    if not os.path.exists(NLP_DB_PATH):
        return None
    return sqlite3.connect(NLP_DB_PATH, check_same_thread=False)


@st.cache_data
def get_filter_options():
    """Compile distinct categories and authors across all partitions for filters."""
    from storybuilder.downloader import db as storybuilder_db

    # Expected optimization impact: Resolving categories and authors across M year partitions
    # O(2 * M) individual DB queries -> 2 queries using ATTACH DATABASE.
    # Significantly improves the startup time of the dashboard when building the sidebar filters.
    categories = set()
    authors = set()
    # Get unique categories
    cat_results = storybuilder_db.execute_all_partitions("SELECT DISTINCT category FROM {table}")
    for r in cat_results:
        if r.get("category"):
            categories.add(r["category"])

    # Get unique authors
    auth_results = storybuilder_db.execute_all_partitions("SELECT DISTINCT author_name FROM {table}")
    for r in auth_results:
        if r.get("author_name"):
            authors.add(r["author_name"])
    return sorted(list(categories)), sorted(list(authors))


@st.cache_data
def load_archive_stats():
    """Pre-aggregate stats across all partition databases for the visualizations."""
    db_files = get_db_files()
    year_stats = []
    category_counts = {}
    author_counts = {}
    word_counts = []
    bracket_counts = {
        "Short (<1K)": 0,
        "Medium-Short (1K-5K)": 0,
        "Medium (5K-10K)": 0,
        "Medium-Long (10K-20K)": 0,
        "Long (20K-50K)": 0,
        "Epic (>50K)": 0,
    }
    for db in db_files:
        year_name = Path(db).stem
        try:
            conn = sqlite3.connect(db)
            cursor = conn.cursor()

            # Year level summary
            cursor.execute("SELECT COUNT(*), SUM(word_count) FROM stories")
            cnt, words = cursor.fetchone()
            if cnt:
                year_stats.append(
                    {
                        "Year": int(year_name),
                        "Stories Count": cnt,
                        "Total Words": words or 0,
                    }
                )
            # Categories summary
            cursor.execute("SELECT category, COUNT(*) FROM stories GROUP BY category")
            for cat, count in cursor.fetchall():
                if cat:
                    category_counts[cat] = category_counts.get(cat, 0) + count

            # Top authors
            cursor.execute(
                "SELECT author_name, COUNT(*) FROM stories GROUP BY author_name"
            )
            for auth, count in cursor.fetchall():
                if auth:
                    author_counts[auth] = author_counts.get(auth, 0) + count

            # Word counts sample for distribution
            cursor.execute("SELECT word_count FROM stories")
            word_counts.extend([r[0] for r in cursor.fetchall()])

            # Word count bracket distribution (binned at SQL level; NULLs excluded)
            cursor.execute(
                """
                SELECT
                    CASE
                        WHEN word_count < 1000 THEN 'Short (<1K)'
                        WHEN word_count < 5000 THEN 'Medium-Short (1K-5K)'
                        WHEN word_count < 10000 THEN 'Medium (5K-10K)'
                        WHEN word_count < 20000 THEN 'Medium-Long (10K-20K)'
                        WHEN word_count < 50000 THEN 'Long (20K-50K)'
                        ELSE 'Epic (>50K)'
                    END AS bracket,
                    COUNT(*)
                FROM stories
                WHERE word_count IS NOT NULL
                GROUP BY bracket
                """
            )
            for bracket, count in cursor.fetchall():
                if bracket in bracket_counts:
                    bracket_counts[bracket] += count
            conn.close()
        except sqlite3.Error:
            pass

    df_years = pd.DataFrame(year_stats)
    df_cats = pd.DataFrame(
        list(category_counts.items()), columns=["Category", "Count"]
    ).sort_values("Count", ascending=False)
    df_auths = pd.DataFrame(
        list(author_counts.items()), columns=["Author", "Count"]
    ).sort_values("Count", ascending=False)
    return df_years, df_cats, df_auths, df_words

    order = [
        "Short (<1K)",
        "Medium-Short (1K-5K)",
        "Medium (5K-10K)",
        "Medium-Long (10K-20K)",
        "Long (20K-50K)",
        "Epic (>50K)",
    ]
    df_words = pd.DataFrame(
        [{"Bracket": b, "Stories": bracket_counts[b]} for b in order]
    )

    return df_years, df_cats, df_auths, df_words


# ------------------------------------------------------------------------------
# CORE SEARCH & QUERY ENGINE
# ------------------------------------------------------------------------------


def query_stories(
    fts_query="",
    category="All",
    author="All",
    year_range=None,
    entity_text="",
    entity_label="PERSON",
    limit=100,
):
    results = []

    # 1. Filter by entity first if specified
    entity_suffixes = None
    if entity_text:
        nlp_conn = get_nlp_conn()
        if nlp_conn:
            cursor = nlp_conn.cursor()
            # Match text and label
            cursor.execute(
                """
                SELECT filepath FROM stories s
                JOIN entities e ON s.id = e.story_id
                WHERE e.text LIKE ? AND e.label = ?
                """,
                (f"%{entity_text}%", entity_label),
            )
            entity_suffixes = []
            for r in cursor.fetchall():
                parts = Path(r[0]).parts
                if len(parts) >= 3:
                    entity_suffixes.append("/".join(parts[-3:]))

    from storybuilder.downloader import db as storybuilder_db

    date_from = None
    date_to = None
    if year_range:
        date_from = f"{year_range[0]}-01-01"
        date_to = f"{year_range[1]}-12-31"

    # Use central search API
    raw_results = storybuilder_db.search_all_partitions(
        fts_query=fts_query,
        category=category,
        author=author,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        snippets=True,
    )

    results = []
    for r in raw_results:
        # Re-inject db_year from path or publication_date for dashboard router compatibility
        pub_date = r.get("publication_date")
        db_year = 2026
        if pub_date and len(str(pub_date)) >= 4:
            try:
                db_year = int(str(pub_date)[:4])
            except ValueError:
                pass

        # Check entity suffixes match if filter active
        if entity_suffixes is not None:
            matched_entity = False
            for suffix in entity_suffixes:
                if r["path"].endswith(suffix):
                    matched_entity = True
                    break
            if not matched_entity:
                continue

        r["db_year"] = db_year
        results.append(r)
    return results[:limit]


def get_story_by_path(story_path, db_year):
    """Retrieve full text and details of a single story from its year partition db."""
    db_path = os.path.join(DB_DIR, f"{db_year}.db")
    if not os.path.exists(db_path):
        return None

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stories WHERE path = ?", (story_path,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except sqlite3.Error:
        return None


# ------------------------------------------------------------------------------
# FAVORITES OPERATIONS
# ------------------------------------------------------------------------------


def add_favorite(story_path, title, author, tags, notes):
    conn = get_meta_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO favorites (story_path, title, author, tags, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (story_path, title, author, tags, notes),
        )
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def remove_favorite(story_path):
    conn = get_meta_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM favorites WHERE story_path = ?", (story_path,))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def get_favorites():
    conn = get_meta_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM favorites ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ------------------------------------------------------------------------------
# SIDEBAR NAVIGATION & FILTERS
# ------------------------------------------------------------------------------

st.sidebar.title("📚 StoryBuilder")
st.sidebar.write("---")

# Page Navigation
page = st.sidebar.radio(
    "Navigation",
    [
        "🔍 Search & Explorer",
        "📖 Read Story",
        "⭐ Favorites & Tags",
        "📊 Archive Stats",
    ],
    key="nav_page",
)

# Fetch filter options dynamically
categories_list, authors_list = get_filter_options()

st.sidebar.subheader("Filters")
# Filter variables
selected_category = st.sidebar.selectbox("Category", ["All"] + categories_list)
selected_author = st.sidebar.selectbox("Author", ["All"] + authors_list)

# Year Range Slider
db_files = get_db_files()
if db_files:
    min_year = int(Path(db_files[0]).stem)
    max_year = int(Path(db_files[-1]).stem)
    if min_year == max_year:
        year_range = (min_year, max_year)
        st.sidebar.write(f"Publication Year: {min_year}")
    else:
        year_range = st.sidebar.slider(
            "Publication Year Range",
            min_year,
            max_year,
            (min_year, max_year),
        )
else:
    year_range = (1990, 2026)

# Named Entity Filter Sub-section
st.sidebar.markdown("---")
st.sidebar.subheader("Entity Filter (spaCy)")
entity_label_select = st.sidebar.selectbox(
    "Entity Label",
    ["PERSON", "NORP", "GPE", "LOC", "ORG", "FAC", "EVENT", "PRODUCT", "WORK_OF_ART"],
)
entity_text_input = st.sidebar.text_input("Entity Text (e.g. character name)", "")

# ------------------------------------------------------------------------------
# PAGES LOGIC
# ------------------------------------------------------------------------------

# Initialize selected_story in session state
if "selected_story_path" not in st.session_state:
    st.session_state.selected_story_path = None
if "selected_story_year" not in st.session_state:
    st.session_state.selected_story_year = None

# -- PAGE 1: SEARCH & EXPLORER --
if page == "🔍 Search & Explorer":
    st.title("🔍 Story Archive Explorer")
    st.write("Browse, search and filter the narrative archives.")

    fts_input = st.text_input(
        "Full-Text Search (FTS5 syntax, e.g. vampire OR werewolf)", ""
    )

    st.markdown("---")

    with st.spinner("Searching records..."):
        search_results = query_stories(
            fts_query=fts_input,
            category=selected_category,
            author=selected_author,
            year_range=year_range,
            entity_text=entity_text_input,
            entity_label=entity_label_select,
        )

    st.subheader(f"Found {len(search_results)} Result(s)")

    for res in search_results:
        # Create a container for the card styling
        card_html = f"""
        <div class="story-card">
            <h4>{html.escape(res["title"] or "Untitled")}</h4>
            <p style='color: #a9b6d8; font-size: 0.95rem; margin-bottom: 8px;'>
                <b>Author:</b> {html.escape(res["author_name"] or "Unknown")} |
                <b>Category:</b> {html.escape(res["category"] or "Unknown")} |
                <b>Published:</b> {html.escape(str(res["publication_date"] or "Unknown"))} |
                <b>Words:</b> {res["word_count"]:,}
            </p>
        """

        # Display highlighted snippets if any
        if res.get("snippet"):
            snippet_cleaned = res["snippet"].replace("___HIGHLIGHT_START___", "<span class='highlight'>").replace("___HIGHLIGHT_END___", "</span>")
            card_html += f"<p style='color: #cbd5e1; font-style: italic; font-size: 0.92rem; background: rgba(0, 0, 0, 0.2); padding: 8px; border-radius: 6px;'>... {snippet_cleaned} ...</p>"

        card_html += "</div>"
        st.markdown(card_html, unsafe_allow_html=True)

        # Action buttons on the card
        col1, col2 = st.columns([1, 8])
        with col1:
            if st.button("Read", key=f"read_{res['path']}_{res['db_year']}"):
                st.session_state.selected_story_path = res["path"]
                st.session_state.selected_story_year = res["db_year"]
                # Programmatically update radio key by modifying query params or session state navigation
                st.query_params["nav_page"] = "📖 Read Story"
                st.rerun()
        st.write("")

# -- PAGE 2: READ STORY --
elif page == "📖 Read Story":
    st.title("📖 Story Reader")

    if not st.session_state.selected_story_path:
        st.warning(
            "No story selected. Please go to 'Search & Explorer' first to pick a story."
        )
    else:
        story = get_story_by_path(
            st.session_state.selected_story_path, st.session_state.selected_story_year
        )
        if not story:
            st.error("Error loading story contents.")
        else:
            # Grid for title and actions
            col_title, col_actions = st.columns([3, 1])
            with col_title:
                st.header(story["title"])
                st.subheader(f"By {story['author_name'] or 'Unknown'}")

            with col_actions:
                # Check if already favorited
                favorites = get_favorites()
                is_fav = any(f["story_path"] == story["path"] for f in favorites)

                # Setup tag editor inside expanding drawer/expander
                with st.expander("⭐ Favorites & Notes", expanded=is_fav):
                    fav_tags = st.text_input(
                        "Tags (comma separated)",
                        "favorite"
                        if not is_fav
                        else next(
                            (
                                f["tags"]
                                for f in favorites
                                if f["story_path"] == story["path"]
                            ),
                            "",
                        ),
                    )
                    fav_notes = st.text_area(
                        "Notes",
                        ""
                        if not is_fav
                        else next(
                            (
                                f["notes"] or ""
                                for f in favorites
                                if f["story_path"] == story["path"]
                            ),
                            "",
                        ),
                    )

                    if is_fav:
                        if st.button("Update Info"):
                            add_favorite(
                                story["path"],
                                story["title"],
                                story["author_name"],
                                fav_tags,
                                fav_notes,
                            )
                            st.success("Updated!")
                        if st.button("Remove from Favorites"):
                            remove_favorite(story["path"])
                            st.success("Removed!")
                            st.rerun()
                    else:
                        if st.button("Add to Favorites"):
                            add_favorite(
                                story["path"],
                                story["title"],
                                story["author_name"],
                                fav_tags,
                                fav_notes,
                            )
                            st.success("Added!")
                            st.rerun()

                # Export to Markdown Button
                md_content = f"""# {story["title"]}
**Author:** {story["author_name"] or "Unknown"}
**Category:** {story["category"]}
**Published:** {story["publication_date"] or "Unknown"}
**URL:** {story["url"] or "N/A"}

---

{story["content"]}
"""
                st.download_button(
                    label="📥 Export Markdown",
                    data=md_content,
                    file_name=f"{story['story_slug'] or 'story'}.md",
                    mime="text/markdown",
                )

            st.write(
                f"**Category:** `{story['category']}` | **Published:** `{story['publication_date'] or 'Unknown'}` | **Words:** `{story['word_count']:,}`"
            )
            st.markdown("---")

            # Story Content Display
            st.markdown(story["content"])

# -- PAGE 3: FAVORITES & TAGS --
elif page == "⭐ Favorites & Tags":
    st.title("⭐ Favorites & Tags")
    st.write("Browse and manage stories you have bookmarked.")

    favorites = get_favorites()
    if not favorites:
        st.info(
            "You haven't bookmarked any stories yet. Read a story and add it to favorites!"
        )
    else:
        # Get unique tags
        all_tags = set()
        for f in favorites:
            if f["tags"]:
                for t in f["tags"].split(","):
                    all_tags.add(t.strip())

        # Tag filter selector
        filter_tag = st.selectbox(
            "Filter Favorites by Tag", ["All"] + sorted(list(all_tags))
        )

        st.write("---")
        # Expected optimization impact: Resolving N favorite stories in M year partitions
        # O(N * M) individual DB queries -> O(M) queries with IN clauses.
        # Significantly improves load time of the Favorites tab, reducing it from seconds to milliseconds.
        fav_paths = [f["story_path"] for f in favorites]
        path_to_db_year = {}
        if fav_paths:
            for y_db in get_db_files():
                y = int(Path(y_db).stem)
                conn = sqlite3.connect(y_db)
                try:
                    # chunking just in case of very large favorites lists
                    chunk_size = 900
                    for i in range(0, len(fav_paths), chunk_size):
                        chunk = fav_paths[i : i + chunk_size]
                        placeholders = ",".join("?" * len(chunk))
                        res = (
                            conn.cursor()
                            .execute(
                                f"SELECT path FROM stories WHERE path IN ({placeholders})",
                                chunk,
                            )
                            .fetchall()
                        )
                        for (p,) in res:
                            path_to_db_year[p] = y
                except sqlite3.Error as e:
                    st.warning(
                        f"Could not resolve story paths from database '{y_db}': {e}"
                    )
                finally:
                    conn.close()
        # Display favorites
        for f in favorites:
            # Filter by tag if needed
            if filter_tag != "All" and f["tags"]:
                tags_list = [t.strip() for t in f["tags"].split(",")]
                if filter_tag not in tags_list:
                    continue
            elif filter_tag != "All" and not f["tags"]:
                continue

            with st.container():
                st.markdown(
                     f"""
                    <div class='story-card'>
                        <h4>{f['title']}</h4>
                        <p style='color: #a9b6d8; font-size: 0.95rem; margin-bottom: 4px;'><b>Author:</b> {f['author'] or 'Unknown'}</p>
                        <p style='font-size: 0.9rem;'><span class='highlight'>Tags:</span> {f['tags'] or 'None'}</p>
                        <p style='font-size: 0.9rem; color: #cbd5e1;'><i>Notes:</i> {f['notes'] or 'None'}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                col1, col2 = st.columns([1, 8])
                with col1:
                    # Attempt to resolve database year based on path to load it in reader
                    db_year = path_to_db_year.get(
                        f["story_path"], 2026
                    )  # Default fallback
                    if st.button("Read", key=f"read_fav_{f['story_path']}"):
                        st.session_state.selected_story_path = f["story_path"]
                        st.session_state.selected_story_year = db_year
                        st.query_params["nav_page"] = "📖 Read Story"
                        st.rerun()
                st.write("")

# -- PAGE 4: ARCHIVE STATS --
elif page == "📊 Archive Stats":
    st.title("📊 Archive Insights & Statistics")
    st.write("Detailed statistics and distributions for the entire story archive.")

    with st.spinner("Compiling database metrics..."):
        df_years, df_cats, df_auths, df_words = load_archive_stats()
    st.markdown("---")

    # Overview metrics row
    total_stories = df_years["Stories Count"].sum()
    total_words = df_years["Total Words"].sum()

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Total Stories", f"{total_stories:,}")
    col_m2.metric("Total Archive Words", f"{total_words:,}")
    col_m3.metric("Average Story Length", f"{total_words // total_stories:,} words")

    st.markdown("---")

    # 1. Timeline Chart
    st.subheader("📈 Publications Timeline (1990 - 2026)")
    fig_line = px.line(
        df_years,
        x="Year",
        y="Stories Count",
        title="Story Publications Per Year",
        markers=True,
    )
    fig_line.update_layout(
        template="plotly_dark", plot_bgcolor="#09101f", paper_bgcolor="#09101f"
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # 2. Categories & Authors Charts
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("🏷️ Top 15 Categories")
        fig_cat = px.bar(
            df_cats.head(15),
            x="Count",
            y="Category",
            orientation="h",
            title="Story Counts by Category",
        )
        fig_cat.update_layout(
            template="plotly_dark",
            plot_bgcolor="#09101f",
            paper_bgcolor="#09101f",
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    with col_right:
        st.subheader("✍️ Top 15 Authors")
        fig_auth = px.bar(
            df_auths.head(15),
            x="Count",
            y="Author",
            orientation="h",
            title="Story Counts by Author",
        )
        fig_auth.update_layout(
            template="plotly_dark",
            plot_bgcolor="#09101f",
            paper_bgcolor="#09101f",
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig_auth, use_container_width=True)

    # 3. Word Count Bracket Distribution
    st.subheader("📐 Story Length Distribution")
    fig_words = px.bar(
        df_words,
        x="Bracket",
        y="Stories",
        title="Story Word Count Distribution Bracket",
    )
    fig_words.update_layout(
        template="plotly_dark", plot_bgcolor="#09101f", paper_bgcolor="#09101f"
    )
    st.plotly_chart(fig_words, use_container_width=True)
