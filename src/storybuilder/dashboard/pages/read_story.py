import textwrap

import streamlit as st

from storybuilder.analytics import capture_event
from storybuilder.dashboard.data import add_favorite
from storybuilder.dashboard.data import get_favorites
from storybuilder.dashboard.data import get_story_by_path
from storybuilder.dashboard.data import remove_favorite


def render_read_story() -> None:
	"""Render the Read Story page."""
	st.title("📖 Story Reader")

	if not st.session_state.selected_story_path:
		st.warning(
			"No story selected. Please go to 'Search & Explorer' first to pick a story.",
		)
		return

	story = get_story_by_path(
		st.session_state.selected_story_path,
		st.session_state.selected_story_year,
	)
	if not story:
		st.error("Error loading story contents.")
		return

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
					(f["tags"] for f in favorites if f["story_path"] == story["path"]),
					"",
				),
			)
			fav_notes = st.text_area(
				"Notes",
				""
				if not is_fav
				else next(
					(f["notes"] or "" for f in favorites if f["story_path"] == story["path"]),
					"",
				),
			)

			favorite_properties = {
				"tag_count": len([tag for tag in fav_tags.split(",") if tag.strip()]),
				"has_notes": bool(fav_notes.strip()),
				"word_count": dict(story).get("word_count") or 0,
			}
			if is_fav:
				if st.button("Update Info"):
					updated = add_favorite(
						story["path"],
						story["title"],
						story["author_name"],
						fav_tags,
						fav_notes,
					)
					if updated:
						capture_event("favorite_updated", favorite_properties)
						st.success("Updated!")
					else:
						st.error("Could not update favorite.")
				if st.button("Remove from Favorites"):
					if remove_favorite(story["path"]):
						capture_event("favorite_removed", favorite_properties)
						st.success("Removed!")
						st.rerun()
					else:
						st.error("Could not remove favorite.")
			elif st.button("Add to Favorites"):
				added = add_favorite(
					story["path"],
					story["title"],
					story["author_name"],
					fav_tags,
					fav_notes,
				)
				if added:
					capture_event("favorite_added", favorite_properties)
					st.success("Added!")
					st.rerun()
				else:
					st.error("Could not add favorite.")

		# Export to Markdown Button
		header = textwrap.dedent(f"""
            # {story["title"]}
            **Author:** {story["author_name"] or "Unknown"}
            **Category:** {story["category"]}
            **Published:** {story["publication_date"] or "Unknown"}
            **URL:** {story["url"] or "N/A"}

            ---
        """).lstrip()

		md_content = f"{header}\n{story['content']}"
		st.download_button(
			label="📥 Export Markdown",
			data=md_content,
			file_name=f"{story['story_slug'] or 'story'}.md",
			mime="text/markdown",
		)

	word_count = dict(story).get("word_count") or 0
	st.write(
		f"**Category:** `{story['category']}` | "
		f"**Published:** `{story['publication_date'] or 'Unknown'}` | "
		f"**Words:** `{word_count:,}`",
	)
	st.markdown("---")

	# Story Content Display
	st.markdown(story["content"])
