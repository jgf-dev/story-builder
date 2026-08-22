from _typeshed import Incomplete

import json
import os
import pathlib
import threading
import time

print_lock: LockType
cache_lock: LockType
metadata_cache: Incomplete


def safe_print(*args: Incomplete, **kwargs: Incomplete) -> None: ...


def load_cache(cache_dir: Incomplete = "stories/db") -> None: ...


def save_cache(cache_dir: Incomplete = "stories/db") -> None: ...
