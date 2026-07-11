"""Thin re-export so that the ``genai-tts`` console script declared in
``pyproject.toml`` (``storybuilder.genai.tts:main``) resolves correctly."""

from storybuilder.genai.client import main


__all__ = ["main"]
