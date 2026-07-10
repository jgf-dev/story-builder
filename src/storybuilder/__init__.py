import importlib

from . import agents
from . import analysis
from . import downloader
from . import genai


__all__ = ["agents", "analysis", "downloader", "genai"]






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
