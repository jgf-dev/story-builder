from _typeshed import Incomplete

import argparse
from argparse import Namespace
from pathlib import Path
import chromadb
import numpy as np
import torch
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from sentence_transformers import SentenceTransformer
from tqdm import tqdm


def get_chunks(text: str, chunk_size: Incomplete = 200) -> list[str]: ...


def parse_args() -> Namespace: ...


def setup_collections(db_path: Incomplete) -> tuple[ClientAPI, Collection, Collection]: ...


def process_story(filepath_str: str, collection_chunks: Collection, collection_averages: Collection, model: SentenceTransformer) -> bool: ...


def main() -> None: ...
