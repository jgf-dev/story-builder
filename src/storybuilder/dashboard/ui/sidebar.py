from pathlib import Path
<<<<<<< HEAD
<<<<<<< HEAD
import streamlit as st

from storybuilder.dashboard.data import get_filter_options, get_db_files
=======

import streamlit as st

from storybuilder.dashboard.data import get_db_files
from storybuilder.dashboard.data import get_filter_options
>>>>>>> palette-fix-duplicate-file-input-1065389564287363483
=======
import streamlit as st

from storybuilder.dashboard.data import get_filter_options, get_db_files
>>>>>>> palette/fix-duplicate-file-input-14315194890274537724


def render_sidebar() -> tuple[str, dict]:
    """Render the sidebar navigation and search filters.

    Returns:
        tuple[str, dict]: (selected_page_name, filter_parameters_dict)
    """
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
    selected_category = st.sidebar.selectbox("Category", ["All", *categories_list])
    selected_author = st.sidebar.selectbox("Author", ["All", *authors_list])

    # Year Range Slider
    db_files = get_db_files()
    if db_files:
        try:
            min_year = int(Path(db_files[0]).stem)
            max_year = int(Path(db_files[-1]).stem)
        except ValueError:
            min_year, max_year = 1990, 2026

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

    filters = {
        "category": selected_category,
        "author": selected_author,
        "year_range": year_range,
        "entity_label": entity_label_select,
        "entity_text": entity_text_input,
    }

    return page, filters
