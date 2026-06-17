# StoryBuilder

## Project Overview

StoryBuilder is a Python toolkit for analyzing, embedding, and generating audio from narrative fiction (text stories). It provides a pipeline for:

1. **NLP Analysis** — Extract named entities (people, places, organizations) and compute per-sentence sentiment scores using spaCy + HuggingFace transformers.
2. **Embedding & Similarity** — Generate sentence-transformer embeddings for story chunks, store them in ChromaDB, and find semantically similar stories.
3. **Narrative Arc Visualization** — Plot emotional trajectories (overall and per-character) as interactive Plotly charts, and cluster stories into narrative archetypes via K-Means.
4. **t-SNE Visualization** — Project story embeddings into 2D space colored by subcategory.
5. **Text-to-Speech** — Test multi-speaker audio generation via Google Gemini's TTS model.
6. **Bedrock Integration** — Invoke AWS Bedrock AgentCore harnesses.

### Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12+ |
| Package manager | uv (pyproject.toml + uv_build) |
| NLP | spaCy (GPU-enabled), HuggingFace transformers |
| Embeddings | sentence-transformers, ChromaDB |
| Visualization | Plotly (interactive HTML), matplotlib, scikit-learn (t-SNE, K-Means) |
| TTS | Google GenAI (gemini-3.1-flash-tts-preview) |
| Cloud | AWS Bedrock AgentCore, Boto3 |
| Data | SQLite (sentiment_analysis.db, nlp_analysis.db) |

## Directory Structure

```
storybuilder/
├── main.py                      # Entry point stub
├── boto.py                      # AWS Bedrock AgentCore harness invocation
├── test_voices.py               # Gemini multi-speaker TTS test
├── analyze_sentiment.py         # Sentiment + entity extraction → SQLite
├── extract_entities.py          # Named entity extraction → SQLite
├── generate_embeddings.py       # Story embeddings → ChromaDB
├── find_similar.py              # Similarity search via ChromaDB
├── compare_narratives.py        # K-Means clustering of narrative arcs
├── visualize_arcs.py            # Per-story emotional trajectory plots
├── visualize_tsne.py            # t-SNE 2D projection of story embeddings
├── sentiment_analysis.db        # Output: sentiment + entity data
├── nlp_analysis.db              # Output: entity frequency data
├── chroma_db/                   # Output: ChromaDB vector store
├── tsne_visualization.html      # Output: t-SNE interactive plot
├── pyproject.toml               # Project definition + dependencies
└── .agent/skills/               # Agent skills (TTS prompt splitter, etc.)
```

## Running the Pipeline

### Prerequisites

```bash
# Install dependencies (uses uv)
uv sync

# Download spaCy models
python -m spacy download en_core_web_sm
python -m spacy download en_core_web_lg

# Create .env with API keys (GEMINI_API_KEY, etc.)
```

### Analysis Pipeline (typical order)

1. **Extract entities** from raw story text files:
   ```bash
   python extract_entities.py --stories-dir nifty_stories --gpu
   ```

2. **Analyze sentiment** (multi-chapter stories):
   ```bash
   python analyze_sentiment.py --stories-dir test_stories --gpu
   ```

3. **Generate embeddings** for similarity search:
   ```bash
   python generate_embeddings.py --stories-dir test_stories
   ```

4. **Find similar stories**:
   ```bash
   python find_similar.py "test_stories/gay/incest/some-story/some-story-1.txt"
   ```

5. **Visualize a narrative arc**:
   ```bash
   python visualize_arcs.py --story "some-story" --window 100
   ```

6. **Compare narrative archetypes** (clusters):
   ```bash
   python compare_narratives.py --clusters 4
   ```

7. **t-SNE visualization**:
   ```bash
   python visualize_tsne.py --perplexity 1000
   ```

8. **Test multi-speaker TTS**:
   ```bash
   python test_voices.py
   ```

### CLI Entry Point

The project defines a `storybuilder` CLI script in pyproject.toml:
```
storybuilder = "storybuilder.downloader.cli:main"
```
This references a `storybuilder.downloader.cli` module that may not yet exist in the repo (the package source is not present at the top level).

## Key Design Patterns

- **SQLite as analysis datastore**: Both `analyze_sentiment.py` and `extract_entities.py` use separate SQLite databases with idempotent inserts (skip already-processed files).
- **ChromaDB for vector search**: Embeddings are stored as both per-chunk (`story_chunks` collection) and per-story averages (`story_averages` collection).
- **GPU-first**: spaCy and sentence-transformers default to CUDA when available.
- **Interactive HTML output**: All visualizations use Plotly dark theme and export to self-contained HTML files.
- **Argparse everywhere**: Every script is a standalone CLI tool with sensible defaults.

## Git Conventions

- Branch: `main`
- Recent commits follow conventional commits (`feat:`, `fix:`)
- Story content lives under `src/stories/` (currently deleted/modified in working tree)
