import html

import streamlit as st

from storybuilder.dashboard.data import StorySearchQuery, query_stories


def render_search_explorer(filters: dict) -> None:
    """Render the Search & Explorer page.

    Args:
        filters (dict): Filter parameters dictionary from the sidebar.
    """
    st.title("🔍 Story Archive Explorer")
    st.write("Browse, search and filter the narrative archives.")

    fts_input = st.text_input(
        "Full-Text Search (FTS5 syntax, e.g. vampire OR werewolf)",
        "",
    )

    st.markdown("---")

    with st.spinner("Searching records..."):
        search_results = query_stories(
            StorySearchQuery(
                fts_query=fts_input,
                category=filters["category"],
                author=filters["author"],
                year_range=filters["year_range"],
                entity_text=filters["entity_text"],
                entity_label=filters["entity_label"],
            ),
        )

    st.subheader(f"Found {len(search_results)} Result(s)")

    for res in search_results:
        # Create a container for the card styling
        safe_title = html.escape(res["title"] or "")
        safe_author = html.escape(res["author_name"] or "Unknown")
        safe_category = html.escape(res["category"] or "")
        safe_pub_date = html.escape(str(res["publication_date"] or "Unknown"))
        card_html = f"""
        <div class="story-card">
            <h4>{safe_title}</h4>
            <p style='color: #a9b6d8; font-size: 0.95rem; margin-bottom: 8px;'>
                <b>Author:</b> {safe_author} |
                <b>Category:</b> {safe_category} |
                <b>Published:</b> {safe_pub_date} |
                <b>Words:</b> {(res.get("word_count") or 0):,}

            </p>
        """

        # Display highlighted snippets if any
        if res.get("snippet"):
            # Escape the snippet first, then replace the placeholder highlight markers with actual HTML span tags
            snippet_escaped = html.escape(res["snippet"])
            snippet_cleaned = snippet_escaped.replace("___HIGHLIGHT_START___", "<span class='highlight'>").replace(
                "___HIGHLIGHT_END___",
                "</span>",
            )

            card_html += "<p style='color: #cbd5e1; font-style: italic; font-size: 0.92rem; padding: 8px;"
            card_html += f" background: rgba(0, 0, 0, 0.2); border-radius: 6px;'>... {snippet_cleaned} ...</p>"
        card_html += "</div>"
        st.markdown(card_html, unsafe_allow_html=True)

        # Action buttons on the card
        col1, _col2 = st.columns([1, 8])
        with col1:
            if st.button("Read", key=f"read_{res['path']}_{res['db_year']}"):
                st.session_state.selected_story_path = res["path"]
                st.session_state.selected_story_year = res["db_year"]
                # Programmatically update radio key by modifying query params and session state navigation
                st.session_state["nav_page"] = "📖 Read Story"
                st.rerun()
        st.write("")
