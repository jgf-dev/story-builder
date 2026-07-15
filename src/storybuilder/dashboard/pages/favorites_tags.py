import datetime
import html

import streamlit as st

from storybuilder.dashboard.data import get_favorites, get_favorites_publication_years


def render_favorites_tags() -> None:
    """Render the Favorites & Tags page."""
    st.title("⭐ Favorites & Tags")
    st.write("Browse and manage stories you have bookmarked.")

    favorites = get_favorites()
    if not favorites:
        st.info("You haven't bookmarked any stories yet. Read a story and add it to favorites!")
        return

    # Get unique tags
    all_tags = set()
    for f in favorites:
        if f["tags"]:
            all_tags.update(t.strip() for t in f["tags"].split(","))

    # Tag filter selector
    filter_tag = st.selectbox("Filter Favorites by Tag", ["All", *sorted(all_tags)])

    st.write("---")

    current_year = datetime.datetime.now(datetime.UTC).year
    fav_paths = [f["story_path"] for f in favorites]
    path_to_db_year = get_favorites_publication_years(fav_paths)

    # Display favorites
    for f in favorites:
        # Filter by tag if needed
        if filter_tag != "All":
            if not f["tags"]:
                continue
            tags_list = [t.strip() for t in f["tags"].split(",")]
            if filter_tag not in tags_list:
                continue

        with st.container():
            safe_fav_title = html.escape(f["title"] or "")
            safe_fav_author = html.escape(f["author"] or "Unknown")
            safe_fav_tags = html.escape(f["tags"] or "None")
            safe_fav_notes = html.escape(f["notes"] or "None")

            card_html = (
                "<div class='story-card'>\n"
                f"    <h4>{safe_fav_title}</h4>\n"
                "    <p style='color: #a9b6d8; font-size: 0.95rem; margin-bottom: 4px;'>"
                f"<b>Author:</b> {safe_fav_author}</p>\n"
                f"    <p style='font-size: 0.9rem;'><span class='highlight'>Tags:</span> {safe_fav_tags}</p>\n"
                f"    <p style='font-size: 0.9rem; color: #cbd5e1;'><i>Notes:</i> {safe_fav_notes}</p>\n"
                "</div>"
            )
            st.markdown(card_html, unsafe_allow_html=True)
            col1, _col2 = st.columns([1, 8])
            with col1:
                # Attempt to resolve database year based on path to load it in reader
                db_year = path_to_db_year.get(f["story_path"], current_year)
                if st.button("Read", key=f"read_fav_{f['story_path']}"):
                    st.session_state.selected_story_path = f["story_path"]
                    st.session_state.selected_story_year = db_year
                    st.session_state["nav_page"] = "📖 Read Story"

                    st.query_params["nav_page"] = "📖 Read Story"
                    st.rerun()
            st.write("")
