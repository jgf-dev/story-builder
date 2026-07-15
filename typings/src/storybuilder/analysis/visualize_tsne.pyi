import argparse
import chromadb
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.io as pio
from sklearn.manifold import TSNE


def parse_args() -> argparse.Namespace: ...


def fetch_embeddings(db_path: str) -> tuple[list[str], np.ndarray, list[dict]]: ...


def run_tsne(embeddings: np.ndarray, perplexity_arg: float) -> np.ndarray: ...


def extract_labels(ids: list[str]) -> tuple[list[str], list[str]]: ...


def create_and_save_plot(embeddings_2d: np.ndarray, ids: list[str], short_names: list[str], subcategories: list[str], output_path: str) -> None: ...


def main() -> None: ...
