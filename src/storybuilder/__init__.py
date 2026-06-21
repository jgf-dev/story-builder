from . import agents, analysis, downloader, genai


__all__ = ["downloader", "genai", "agents", "analysis"]

"""
def __getattr__(name):
    if name == "cartesia":
        from . import cartesia as _cartesia

        return _cartesia
    if name == "downloader":
        from . import downloader as _downloader

        return _downloader
    if name == "utils":
        from . import utils as _utils

        return _utils
    if name == "genai":
        from . import genai as _genai

        return _genai
    if name == "agents":
        from . import agents as _agents

        return _agents
    if name == "analysis":
        from . import analysis as _analysis

        return _analysis
    raise AttributeError(f"module 'storybuilder' has no attribute '{name}'")
"""
