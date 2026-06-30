# StoryBuilder

StoryBuilder is an integrated Python toolkit and pipeline designed to scrape, store, analyze, embed, and synthesize audio from narrative fiction. It streamlines NLP-driven narrative analysis and provides deep multi-speaker Text-to-Speech (TTS) capabilities.

---

## 🚀 Key Features

* **Automated Downloader & Scraper**: Robust multi-threaded scraper for [Nifty Archive](https://nifty.org) and [Nifty Search](https://search.niftyarchives.org), including SOCKS5 proxy support, automatic IP rotation, and comprehensive SQLite metadata caching.
* **Idempotent SQLite DB Integration**: Import crawled text, automatically extract authors and structural markers, and enable ultra-fast Full-Text Search (FTS5).
* **NLP & Sentiment Analysis**: Extract named entities (people, places, organizations) and sentence-level sentiment curves using GPU-accelerated spaCy models and HuggingFace transformers.
* **Vector Embeddings & Semantic Search**: Generate sentence-transformer embeddings, persist them in ChromaDB collections, and retrieve semantically similar stories.
* **Interactive Narrative Visualizations**: Generate Plotly-based HTML plots of characters' emotional trajectories (emotional arcs) and t-SNE clustering visualizations.
* **Multi-Speaker TTS Generation**: Intelligently chunk narrative transcripts by scenes and character dialogue, auto-assign voices (Gemini TTS / Cartesia), and output high-quality multi-speaker audio.

---

## 🛠️ Tech Stack

* **Runtime**: Python 3.12+ (managed with `uv` or `uv pip`)
* **NLP**: spaCy, HuggingFace transformers
* **Database**: SQLite (FTS5 + Triggers), ChromaDB vector store
* **Embeddings**: sentence-transformers
* **TTS**: Google GenAI (`gemini-3.1-flash-tts-preview`), Cartesia
* **Visualization**: Plotly, Scikit-learn (K-Means, t-SNE), Matplotlib

---

## 📂 Codebase Directory Structure

```text
storybuilder/
├── pyproject.toml               # Package configuration and dependencies
├── src/                         # Python source package modules
│   └── storybuilder/
│       ├── downloader/          # Scraping, IP rotation, writer, and caching layers
│       ├── analysis/            # Sentiment, entity, embedding, and visualization CLIs
│       ├── genai/               # Google GenAI TTS client & voice assigners
│       └── utils/               # Prompts and common utilities
├── scripts/                     # SQLite database indexing and querying scripts
│   ├── import_to_sqlite.py      # Idempotent DB importer with FTS5 table setup
│   └── story_db.py              # FTS search, retrieval, and stats CLI
└── tests/                       # Unit and integration test suite
```

---

## ⚙️ Setup & Installation

### 1. Synchronize Dependencies

This project uses `uv` for lightning-fast package management:

```bash
uv sync --all-extras --dev
```

*Alternatively, you can install the dependencies via pip:*

```bash
pip install -e .
```

### 2. Download spaCy NLP Models

```bash
python3 -m spacy download en_core_web_sm
python3 -m spacy download en_core_web_lg
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY="your-gemini-key"
# Quota rotation support:
GEMINI_API_KEY_1="your-backup-key-1"
GEMINI_API_KEY_2="your-backup-key-2"

CARTESIA_API_KEY="your-cartesia-key"
```

---

## 🔄 End-to-End Execution Pipeline

To run the full suite from raw extraction to downstream analysis and TTS:

### Step 1: Scrape & Download Stories

Run the downloader using SOCKS5 proxy support and IP rotation:

```bash
storybuilder --category gay --start-date 1990-01-01 --end-date 2025-12-31 --output-dir nifty_stories --socks5-proxy 127.0.0.1:1080 --rotate-on-refusal --max-workers 5
```

### Step 2: Index Content into SQLite

Parse and register the downloaded plain texts into the FTS5-indexed database:

```bash
python3 scripts/import_to_sqlite.py --db stories/stories.db
```

### Step 3: Run NLP Analysis

Compute sentence sentiment and extract named entities:

```bash
python3 -m storybuilder.analysis.analyze_sentiment --stories-dir nifty_stories --gpu
python3 -m storybuilder.analysis.extract_entities --stories-dir nifty_stories --gpu
```

### Step 4: Embed & Search

Generate ChromaDB embeddings and run a similarity query:

```bash
python3 -m storybuilder.analysis.generate_embeddings --stories-dir nifty_stories
python3 -m storybuilder.analysis.find_similar "nifty_stories/gay/subcat/slug/story.txt"
```

### Step 5: Visualize

Generate t-SNE scatter plots and Plotly emotional arc trajectories:

```bash
python3 -m storybuilder.analysis.visualize_arcs --story "story-slug" --window 100
python3 -m storybuilder.analysis.visualize_tsne --perplexity 1000
```

---

## 🧪 Running Tests

The repository contains a highly optimized `unittest` test suite. All network requests and heavy deep-learning model downloads are fully mocked out. This allows you to verify environment correctness and pipeline integrity in seconds without consuming compute quota:

Run the test suite using standard Python unittest:

```bash
PYTHONPATH=src:scripts python3 -m unittest discover -s tests -p "test_*.py" -v
```

Or using `pytest` if available:

```bash
pytest
```
