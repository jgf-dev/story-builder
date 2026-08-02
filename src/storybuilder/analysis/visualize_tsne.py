import argparse

import chromadb
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.io as pio
from sklearn.manifold import TSNE


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Visualize story embeddings using t-SNE.",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="./chroma_db",
        help="Path to the Chroma database.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="tsne_visualization.html",
        help="Output HTML file path.",
    )
    parser.add_argument(
        "--perplexity",
        type=float,
        default=1000.0,
        help="Perplexity for t-SNE (adjust based on dataset size).",
    )
    return parser.parse_args()


def fetch_embeddings(db_path: str) -> tuple[list[str], np.ndarray, list[dict]]:
    chroma_client = chromadb.PersistentClient(path=db_path)

    try:
        collection_averages = chroma_client.get_collection(name="story_averages")
    except Exception:
        print(
            "Error: Could not find 'story_averages' collection. Run generate_embeddings.py first.",
        )
        return [], np.array([]), []

    print("Fetching embeddings from database...")
    data = collection_averages.get(include=["embeddings", "metadatas"])

    ids = data["ids"]
    embeddings = np.array(data["embeddings"])
    metadatas = data["metadatas"]

    return ids, embeddings, metadatas


def run_tsne(embeddings: np.ndarray, perplexity_arg: float) -> np.ndarray:
    perplexity = min(perplexity_arg, max(5.0, len(embeddings) - 1))
    print(f"Running t-SNE dimensionality reduction (perplexity={perplexity})...")
    tsne = TSNE(
        n_components=2,
        perplexity=perplexity,
        random_state=42,
        init="pca",
        learning_rate="auto",
    )
    embeddings_2d = tsne.fit_transform(embeddings)
    return embeddings_2d


def extract_labels(ids: list[str]) -> tuple[list[str], list[str]]:
    short_names = []
    subcategories = []
    for filepath in ids:
        parts = filepath.replace("\\", "/").split("/")
        short_names.append(parts[-1])
        if len(parts) >= 3:
            subcategories.append(parts[2])
        else:
            subcategories.append("unknown")
    return short_names, subcategories


def create_and_save_plot(
    embeddings_2d: np.ndarray,
    ids: list[str],
    short_names: list[str],
    subcategories: list[str],
    output_path: str,
) -> None:
    print("Generating interactive plot...")
    fig = px.scatter(
        x=embeddings_2d[:, 0],
        y=embeddings_2d[:, 1],
        color=subcategories,
        hover_name=short_names,
        hover_data={"filepath": ids, "subcategory": subcategories},
        title="t-SNE Projection of Story Plots by Subcategory",
        labels={
            "x": "t-SNE Dimension 1",
            "y": "t-SNE Dimension 2",
            "color": "Subcategory",
        },
        opacity=0.7,
        template="plotly_dark",
    )

    fig.update_traces(marker={"size": 8, "line": {"width": 1, "color": "DarkSlateGrey"}})

    df = pd.DataFrame.from_records(
        {
            "x": embeddings_2d[:, 0],
            "y": embeddings_2d[:, 1],
            "subcategory": subcategories,
        },
    )
    centroids = df.groupby("subcategory")[["x", "y"]].mean().reset_index()

    for _, row in centroids.iterrows():
        fig.add_annotation(
            x=row["x"],
            y=row["y"],
            text=f"<b>{row['subcategory'].upper()}</b>",
            showarrow=False,
            font={"size": 14, "color": "white"},
            bgcolor="rgba(0,0,0,0.6)",
            bordercolor="white",
            borderwidth=1,
            borderpad=4,
        )

    pio.write_html(fig, file=output_path, auto_open=False)
    print(f"Visualization saved successfully to {output_path}")
    print("Open this file in your web browser to explore the clusters interactively.")


def main() -> None:
    args = parse_args()

    ids, embeddings, _ = fetch_embeddings(args.db_path)

    if len(embeddings) < 2:
        if len(embeddings) > 0:
            print("Error: Need at least 2 stories in the database to run t-SNE.")
        return

    print(f"Loaded {len(embeddings)} story embeddings.")

    embeddings_2d = run_tsne(embeddings, args.perplexity)
    short_names, subcategories = extract_labels(ids)

    create_and_save_plot(embeddings_2d, ids, short_names, subcategories, args.output)


if __name__ == "__main__":
    main()
