import importlib

from . import agents, analysis, downloader, genai

__all__ = ["cartesia", "downloader", "utils", "genai", "agents", "analysis"]

def __getattr__(name):
    if name == "cartesia":
        # Attempt to lazily load cartesia (could be third-party or formerly local)
        try:
            return importlib.import_module(f"{__name__}.cartesia")
        except ImportError:
            return importlib.import_module("cartesia")
    if name == "utils":
        try:
            return importlib.import_module(f"{__name__}.utils")
        except ImportError:
            return importlib.import_module("utils")
    raise AttributeError(f"module 'storybuilder' has no attribute '{name}'")
