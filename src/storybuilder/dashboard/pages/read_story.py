import streamlit as st

<<<<<<< HEAD
from storybuilder.dashboard.data import add_favorite
from storybuilder.dashboard.data import get_favorites
from storybuilder.dashboard.data import get_story_by_path
from storybuilder.dashboard.data import remove_favorite
=======
from storybuilder.dashboard.data import (
    get_story_by_path,
    get_favorites,
    add_favorite,
    remove_favorite,
)
>>>>>>> palette/save-button-tooltip-16022957350325416287


def render_read_story() -> None:
    """Render the Read Story page."""
    st.title("📖 Story Reader")

    if not st.session_state.selected_story_path:
        st.warning(
            "No story selected. Please go to 'Search & Explorer' first to pick a story.",
        )
    else:
        story = get_story_by_path(
            st.session_state.selected_story_path,
            st.session_state.selected_story_year,
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
<<<<<<< HEAD
                            (f["tags"] for f in favorites if f["story_path"] == story["path"]),
=======
                            (
                                f["tags"]
                                for f in favorites
                                if f["story_path"] == story["path"]
                            ),
>>>>>>> palette/save-button-tooltip-16022957350325416287
                            "",
                        ),
                    )
                    fav_notes = st.text_area(
                        "Notes",
                        ""
                        if not is_fav
                        else next(
<<<<<<< HEAD
                            (f["notes"] or "" for f in favorites if f["story_path"] == story["path"]),
=======
                            (
                                f["notes"] or ""
                                for f in favorites
                                if f["story_path"] == story["path"]
                            ),
>>>>>>> palette/save-button-tooltip-16022957350325416287
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
<<<<<<< HEAD
                    elif st.button("Add to Favorites"):
                        add_favorite(
                            story["path"],
                            story["title"],
                            story["author_name"],
                            fav_tags,
                            fav_notes,
                        )
                        st.success("Added!")
                        st.rerun()
=======
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
>>>>>>> palette/save-button-tooltip-16022957350325416287

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
<<<<<<< HEAD
                f"**Category:** `{story['category']}` | **Published:** `{story['publication_date'] or 'Unknown'}` | **Words:** `{story['word_count']:,}`",
=======
                f"**Category:** `{story['category']}` | **Published:** `{story['publication_date'] or 'Unknown'}` | **Words:** `{story['word_count']:,}`"
>>>>>>> palette/save-button-tooltip-16022957350325416287
            )
            st.markdown("---")

            # Story Content Display
            st.markdown(story["content"])
