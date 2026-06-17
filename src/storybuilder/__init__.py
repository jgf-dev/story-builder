# Lazy imports to avoid circular dependency issues
__all__ = ["cartesia", "downloader", "utils"]


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
    raise AttributeError(f"module 'storybuilder' has no attribute '{name}'")
