import argparse
from pathlib import Path

import chromadb
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from tqdm import tqdm


def get_chunks(text, chunk_size=200):
    """Splits text into chunks of approximately `chunk_size` words."""
    words = text.split()
    return [" ".join(words[i: i + chunk_size]) for i in range(0, len(words), chunk_size)]


def main():
    parser = argparse.ArgumentParser(description="Generate embeddings for stories and store in ChromaDB.")
    parser.add_argument("--limit", type=int, default=float("inf"), help="Maximum number of files to process.")
    parser.add_argument("--stories-dir", type=str, default="test_stories", help="Directory containing the text files.")
    parser.add_argument("--db-path", type=str, default="./chroma_db", help="Path to the Chroma database.")
    parser.add_argument("--model", type=str, default="all-MiniLM-L6-v2", help="SentenceTransformer model to use.")
    args = parser.parse_args()

    chroma_client = chromadb.PersistentClient(path=args.db_path)

    collection_chunks = chroma_client.get_or_create_collection(
        name="story_chunks",
        metadata={"hnsw:space": "cosine"}
    )

    collection_averages = chroma_client.get_or_create_collection(
        name="story_averages",
        metadata={"hnsw:space": "cosine"}
    )

    print(f"Loading SentenceTransformer model: {args.model}")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    model = SentenceTransformer(args.model, device=device)

    all_files = list(Path(args.stories_dir).rglob("*.txt"))
    print(f"Found {len(all_files)} total text files.")

    processed_count = 0
    pbar = tqdm(total=min(len(all_files), args.limit), desc="Embedding stories")

    for filepath in all_files:
        filepath_str = str(filepath)
        story_id = filepath_str

        existing = collection_averages.get(ids=[story_id])
        if existing and existing["ids"]:
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()

            chunks = get_chunks(text, chunk_size=250)
            if not chunks:
                continue

            chunk_embeddings = model.encode(chunks, convert_to_numpy=True, show_progress_bar=False)
            chunk_ids = [f"{story_id}_chunk_{i}" for i in range(len(chunks))]
            chunk_metadatas = [{"story_id": story_id, "chunk_index": i} for i in range(len(chunks))]

            collection_chunks.add(
                ids=chunk_ids,
                embeddings=chunk_embeddings.tolist(),
                documents=chunks,
                metadatas=chunk_metadatas
            )

            avg_embedding = np.mean(chunk_embeddings, axis=0)

            collection_averages.add(
                ids=[story_id],
                embeddings=[avg_embedding.tolist()],
                documents=[""],
                metadatas=[{"filepath": filepath_str}]
            )

            processed_count += 1
            pbar.update(1)

            if processed_count >= args.limit:
                break

        except Exception as e:
            print(f"\nError processing {filepath_str}: {e}")

    pbar.close()
    print(f"Finished processing {processed_count} new stories.")


if __name__ == "__main__":
    main()
