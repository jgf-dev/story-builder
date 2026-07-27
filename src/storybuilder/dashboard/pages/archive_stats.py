import datetime

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

    # Guard against empty database
    if df_years.empty or "Stories Count" not in df_years.columns:
        st.info("No archive data available yet.")
        return

    # Overview metrics row
    total_stories = df_years["Stories Count"].sum() if "Stories Count" in df_years.columns else 0
    total_words = df_years["Total Words"].sum() if "Total Words" in df_years.columns else 0

    cols = st.columns(3)
    cols[0].metric("Total Stories", f"{total_stories:,}")
    cols[1].metric("Total Archive Words", f"{total_words:,}")
    cols[2].metric(
        "Average Story Length",
        f"{total_words // total_stories if total_stories > 0 else 0:,} words",
    )
    st.markdown("---")

    # 1. Timeline Chart
    current_year = datetime.datetime.now(datetime.UTC).year
    st.subheader(f"📈 Publications Timeline (1990 - {current_year})")
    fig = px.line(
        df_years,
        x="Year",
        y="Stories Count",
        title="Story Publications Per Year",
        markers=True,
    )
    fig.update_layout(template="plotly_dark", plot_bgcolor="#09101f", paper_bgcolor="#09101f")

    st.plotly_chart(fig, use_container_width=True)

    # 2. Categories & Authors Charts
    chart_cols = st.columns(2)

    with chart_cols[0]:
        st.subheader("🏷️ Top 15 Categories")
        fig = px.bar(
            df_cats.head(15),
            x="Count",
            y="Category",
            orientation="h",
            title="Story Counts by Category",
        )
        fig.update_layout(
            template="plotly_dark",
            plot_bgcolor="#09101f",
            paper_bgcolor="#09101f",
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with chart_cols[1]:
        st.subheader("✍️ Top 15 Authors")
        fig = px.bar(
            df_auths.head(15),
            x="Count",
            y="Author",
            orientation="h",
            title="Story Counts by Author",
        )
        fig.update_layout(
            template="plotly_dark",
            plot_bgcolor="#09101f",
            paper_bgcolor="#09101f",
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig, use_container_width=True)

    # 3. Word Count Bracket Distribution
    st.subheader("📐 Story Length Distribution")
    fig = px.bar(
        df_words,
        x="Bracket",
        y="Stories",
        title="Story Word Count Distribution Bracket",
    )
    fig.update_layout(template="plotly_dark", plot_bgcolor="#09101f", paper_bgcolor="#09101f")

    st.plotly_chart(fig, use_container_width=True)
