import argparse

import chromadb


def main():
    parser = argparse.ArgumentParser(
        description="Find similar stories based on average plot embeddings.",
    )
    parser.add_argument("target_story", type=str, help="Filepath of the target story.")
    parser.add_argument(
        "--db-path",
        type=str,
        default="./chroma_db",
        help="Path to the Chroma database.",
    )
    parser.add_argument("--n-results", type=int, default=5, help="Number of similar stories to return.")
    args = parser.parse_args()

    chroma_client = chromadb.PersistentClient(path=args.db_path)

    try:
        collection_averages = chroma_client.get_collection(name="story_averages")
    except Exception:
        print(
            "Error: Could not find 'story_averages' collection. Run generate_embeddings.py first.",
        )
        return

    result = collection_averages.get(ids=[args.target_story], include=["embeddings"])

    if result is None or result.get("embeddings") is None or len(result["embeddings"]) == 0:
        print(f"Error: Story '{args.target_story}' not found in the database.")
        print("Please ensure you use the exact filepath used during generation.")
        return

    target_embedding = result["embeddings"][0]

    print(f"Finding top {args.n_results} stories similar to: {args.target_story}\n")

    query_results = collection_averages.query(query_embeddings=[target_embedding], n_results=args.n_results + 1)

    for idx, (filepath, distance) in enumerate(
        zip(query_results["ids"][0], query_results["distances"][0], strict=False),
    ):
        if filepath == args.target_story:
            continue

        print(f"{idx}. {filepath}")
        print(f"   Distance (lower is closer): {distance:.4f}\n")


if __name__ == "__main__":
    main()
