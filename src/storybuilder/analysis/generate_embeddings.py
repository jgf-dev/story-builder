import argparse
from argparse import Namespace
from pathlib import Path

import chromadb
import numpy as np
import torch
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from sentence_transformers import SentenceTransformer
from sentence_transformers.sentence_transformer.model import SentenceTransformer
from tqdm import tqdm


def get_chunks(text: str, chunk_size=200) -> list[str]:
	"""Splits text into chunks of approximately `chunk_size` words."""
	words = text.split()
	return [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)]


def parse_args() -> Namespace:
	parser = argparse.ArgumentParser(description="Generate embeddings for stories and store in ChromaDB.")
	parser.add_argument(
		"--limit",
		type=int,
<<<<<<< HEAD
		default=float("inf"),
=======
		default=10**9,
>>>>>>> origin/main
		help="Maximum number of files to process.",
	)
	parser.add_argument(
		"--stories-dir",
		type=str,
		default="test_stories",
		help="Directory containing the text files.",
	)
	parser.add_argument(
		"--db-path",
		type=str,
		default="./chroma_db",
		help="Path to the Chroma database.",
	)
	parser.add_argument(
		"--model",
		type=str,
		default="all-MiniLM-L6-v2",
		help="SentenceTransformer model to use.",
	)
	return parser.parse_args()


def setup_collections(db_path) -> tuple[ClientAPI, Collection, Collection]:
	chroma_client = chromadb.PersistentClient(path=db_path)

	collection_chunks = chroma_client.get_or_create_collection(name="story_chunks", metadata={"hnsw:space": "cosine"})

	collection_averages = chroma_client.get_or_create_collection(
		name="story_averages",
		metadata={"hnsw:space": "cosine"},
	)

	return chroma_client, collection_chunks, collection_averages


def process_story(
	filepath_str: str,
	collection_chunks: Collection,
	collection_averages: Collection,
	model: SentenceTransformer,
) -> bool:
	existing = collection_averages.get(ids=[filepath_str])
	if existing and existing["ids"]:
		return False

	try:
		text = Path(filepath_str).read_text(encoding="utf-8")

		chunks = get_chunks(text, chunk_size=250)
		if not chunks:
			return False

		chunk_embeddings = model.encode(
			chunks,
			convert_to_numpy=True,
			show_progress_bar=False,
		)
		chunk_ids = [f"{filepath_str}_chunk_{i}" for i in range(len(chunks))]
		chunk_metadatas = [{"story_id": filepath_str, "chunk_index": i} for i in range(len(chunks))]

		collection_chunks.add(
			ids=chunk_ids,
			embeddings=chunk_embeddings.tolist(),
			documents=chunks,
			metadatas=chunk_metadatas,  # pyrefly: ignore [bad-argument-type]
		)

		avg_embedding = np.mean(chunk_embeddings, axis=0)

		collection_averages.add(
			ids=[filepath_str],
			embeddings=[avg_embedding.tolist()],
			documents=[""],
			metadatas=[{"filepath": filepath_str}],
		)

		return True

	except Exception as e:
		print(f"\nError processing {filepath_str}: {e}")
		return False


def main() -> None:
	args = parse_args()
	_, collection_chunks, collection_averages = setup_collections(
		args.db_path,
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
		if process_story(str(filepath), collection_chunks, collection_averages, model):
			processed_count += 1
			pbar.update(1)

			if processed_count >= args.limit:
				break

	pbar.close()
	print(f"Finished processing {processed_count} new stories.")


if __name__ == "__main__":
	main()
