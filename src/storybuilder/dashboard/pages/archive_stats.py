import plotly.express as px
import streamlit as st

from storybuilder.dashboard.data import load_archive_stats


def render_archive_stats() -> None:
    """Render the Archive Insights & Statistics page."""
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
    col_m3.metric(
        "Average Story Length",
        f"{total_words // total_stories if total_stories > 0 else 0:,} words",
    )
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
        template="plotly_dark",
        plot_bgcolor="#09101f",
        paper_bgcolor="#09101f",
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
        template="plotly_dark",
        plot_bgcolor="#09101f",
        paper_bgcolor="#09101f",
    )
    st.plotly_chart(fig_words, use_container_width=True)
