#!/usr/bin/env bash
set -euo pipefail

python -m pip install uv
uv sync --all-extras --dev
uv run python -m spacy download en_core_web_sm
uv run python -m spacy download en_core_web_lg
uv run pytest
