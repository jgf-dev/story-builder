import importlib

from . import agents, analysis, downloader, genai


__all__ = ["downloader", "genai", "agents", "analysis"]

def __getattr__(name):
    if name == "cartesia":
        # Attempt to lazily load cartesia (could be third-party or formerly local)
        try:
            from . import cartesia as _cartesia
            return _cartesia
        except ImportError:
            import cartesia as _cartesia
            return _cartesia
    if name == "utils":
        try:
            from . import utils as _utils
            return _utils
        except ImportError:
            import utils as _utils
            return _utils
    raise AttributeError(f"module 'storybuilder' has no attribute '{name}'")
