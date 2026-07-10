import argparse
import sqlite3
from collections import defaultdict

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.interpolate import interp1d
from sklearn.cluster import KMeans


def main():
    parser = argparse.ArgumentParser(
        description="Compare and cluster narrative trajectories.",
    )
    parser.add_argument("--db-path", default="sentiment_analysis.db")
    parser.add_argument(
        "--clusters", type=int, default=4, help="Number of narrative archetypes to find",
    )
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)

    df_stories = pd.read_sql_query(
        "SELECT id, story_dir, subcategory FROM stories", conn,
    )

    if len(df_stories) < args.clusters:
        print(
            f"Error: Not enough stories ({len(df_stories)}) to form {args.clusters} clusters.",
        )
        return

    print(f"Loaded {len(df_stories)} processed stories. Normalizing trajectories...")

    normalized_arcs = []
    story_metadata = []

    for _, row in df_stories.iterrows():
        story_id = row["id"]

        df_sentences = pd.read_sql_query(
            """
            SELECT sentiment_score
            FROM sentences
            WHERE story_id = ?
            ORDER BY chapter_index, sentence_index
        """,
            conn,
            params=(int(story_id),),
        )

        scores = df_sentences["sentiment_score"].values
        n_sentences = len(scores)

        if n_sentences < 20:
            print(f"Skipping {row['story_dir']} (only {n_sentences} sentences)")
            continue

        window = max(5, n_sentences // 20)
        smoothed = (
            pd.Series(scores)
            .rolling(window=window, center=True, min_periods=1)
            .mean()
            .values
        )

        x_orig = np.linspace(0, 1, n_sentences)
        x_new = np.linspace(0, 1, 100)

        interpolator = interp1d(x_orig, smoothed, kind="linear")
        arc_100 = interpolator(x_new)

        normalized_arcs.append(arc_100)
        story_metadata.append(row)

    if not normalized_arcs:
        print("No valid trajectories found.")
        return

    X = np.array(normalized_arcs)

    print(f"Clustering into {args.clusters} narrative archetypes...")
    kmeans = KMeans(n_clusters=args.clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)

    fig = go.Figure()

    cluster_names = [f"Archetype {i + 1}" for i in range(args.clusters)]

    for i in range(args.clusters):
        cluster_arcs = X[labels == i]
        mean_arc = cluster_arcs.mean(axis=0)
        cluster_arcs.std(axis=0)

        x_vals = np.arange(100)

        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=mean_arc,
                mode="lines",
                name=cluster_names[i],
                line=dict(width=4),
            ),
        )

        print(f"\n=== {cluster_names[i]} (N={len(cluster_arcs)}) ===")
        subcats = defaultdict(int)
        for j, lbl in enumerate(labels):
            if lbl == i:
                subcats[story_metadata[j]["subcategory"]] += 1

        for subcat, count in sorted(
            subcats.items(), key=lambda item: item[1], reverse=True,
        ):
            print(f"  - {subcat}: {count} stories")

    fig.update_layout(
        title="Common Narrative Archetypes across Stories",
        xaxis_title="Story Progress (%)",
        yaxis_title="Average Sentiment",
        template="plotly_dark",
        hovermode="x unified",
    )

    out_file = "narrative_archetypes.html"
    fig.write_html(out_file)
    print(f"\nSaved archetype visualization to {out_file}")


if __name__ == "__main__":
    main()
