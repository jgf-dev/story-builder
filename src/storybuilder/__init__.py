"""Top-level package for StoryBuilder."""

from importlib import import_module

__all__ = ["downloader", "genai", "agents", "analysis", "utils"]


def __getattr__(name):
    if name in __all__:
        module = import_module(f".{name}", __name__)
        globals()[name] = module
        return module
    raise AttributeError(f"module 'storybuilder' has no attribute '{name}'")
