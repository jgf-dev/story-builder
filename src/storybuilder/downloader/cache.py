import json
import os
import pathlib
import threading
import time


# Thread locks to serialize stdout print statements and cache access
print_lock = threading.Lock()
cache_lock = threading.Lock()
metadata_cache = {}


def safe_print(*args, **kwargs):
    """
    Thread-safe print to avoid interleaved output.
    """
    with print_lock:
        print(*args, **kwargs)


def load_cache(cache_dir):
    """
    Loads the metadata cache from cache_dir/metadata_cache.json.
    """
    cache_path = os.path.join(cache_dir, "metadata_cache.json")
    if pathlib.Path(cache_path).exists():
        try:
            with pathlib.Path(cache_path).open("r", encoding="utf-8") as f, cache_lock:
                data = json.load(f)
                metadata_cache.clear()
                metadata_cache.update(data)
            safe_print(
                f"Loaded cache from {cache_path} with {len(metadata_cache)} entries.",
            )
        except Exception as e:
            safe_print(f"Warning: Failed to load cache: {e}")
    else:
        safe_print(f"No cache found at {cache_path}")
    for _ in range(10):
        time.sleep(1)
        print(".", end="", flush=True)
    print()


def save_cache(cache_dir):
    """
    Saves the metadata cache to cache_dir/metadata_cache.json.
    """
    cache_path = os.path.join(cache_dir, "metadata_cache.json")
    try:
        pathlib.Path(os.path.dirname(cache_path)).mkdir(exist_ok=True, parents=True)
        with pathlib.Path(cache_path).open("w", encoding="utf-8") as f, cache_lock:
            json.dump(metadata_cache, f, indent=2)
        safe_print(f"Saved metadata cache to {cache_path}")
    except Exception as e:
        safe_print(f"Warning: Failed to save cache: {e}")
