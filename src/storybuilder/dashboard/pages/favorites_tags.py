import html

import streamlit as st

from storybuilder.dashboard.data import get_favorites



def render_favorites_tags() -> None:
    """Render the Favorites & Tags page."""
    st.title("⭐ Favorites & Tags")
    st.write("Browse and manage stories you have bookmarked.")

    favorites = get_favorites()
    if not favorites:
        st.info("You haven't bookmarked any stories yet. Read a story and add it to favorites!")

    else:
        # Get unique tags
        all_tags = set()
        for f in favorites:
            if f["tags"]:
                all_tags.update(t.strip() for t in f["tags"].split(","))

        # Tag filter selector
        filter_tag = st.selectbox("Filter Favorites by Tag", ["All"] + sorted(list(all_tags)))


        st.write("---")
        # Expected optimization impact: Resolving N favorite stories in M year partitions
        # O(N * M) individual DB queries -> O(M) queries with IN clauses.
        # Significantly improves load time of the Favorites tab, reducing it from seconds to milliseconds.
        fav_paths = [f["story_path"] for f in favorites]
        path_to_db_year = {}
        if fav_paths:
            from storybuilder.downloader import db as storybuilder_db

            try:
                placeholders = ",".join("?" for _ in fav_paths)
                rows = storybuilder_db.execute_query(
                    f"SELECT path, publication_date FROM stories WHERE path IN ({placeholders})",
                    params=tuple(fav_paths),
                )
                for row in rows:
                    pub_date = row.get("publication_date")
                    try:
                        y = int(str(pub_date)[:4]) if pub_date and len(str(pub_date)) >= 4 else 2026
                    except ValueError:
                        y = 2026
                    path_to_db_year[row["path"]] = y
            except Exception as e:
                st.warning(f"Could not resolve story paths from database: {e}")


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
                safe_fav_title = html.escape(f["title"] or "")
                safe_fav_author = html.escape(f["author"] or "Unknown")
                safe_fav_tags = html.escape(f["tags"] or "None")
                safe_fav_notes = html.escape(f["notes"] or "None")

                st.markdown(
                    f"""
                    <div class='story-card'>
                        <h4>{safe_fav_title}</h4>
                        <p style='color: #a9b6d8; font-size: 0.95rem; margin-bottom: 4px;'><b>Author:</b> {safe_fav_author}</p>
                        <p style='font-size: 0.9rem;'><span class='highlight'>Tags:</span> {safe_fav_tags}</p>
                        <p style='font-size: 0.9rem; color: #cbd5e1;'><i>Notes:</i> {safe_fav_notes}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                col1, col2 = st.columns([1, 8])
                with col1:
                    # Attempt to resolve database year based on path to load it in reader
                    db_year: str = str(path_to_db_year.get(f["story_path"], 2026))
                    if st.button("Read", key=f"read_fav_{f['story_path']}"):
                        st.session_state.selected_story_path = f["story_path"]
                        st.session_state.selected_story_year = db_year
                        st.session_state["nav_page"] = "📖 Read Story"
                        st.query_params["nav_page"] = "📖 Read Story"
                        st.rerun()
                st.write("")

