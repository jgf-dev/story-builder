from _typeshed import Incomplete

import time
import requests

BASE_URL: Literal['https://nifty.org/nifty/'] = "https://nifty.org/nifty/"
PROXIES: dict[str, str] | None = None
ENABLE_ROTATION: bool = False


def safe_print(*args: Incomplete, **kwargs: Incomplete) -> None: ...


def rotate_windscribe_ip() -> bool: ...


def fetch_page(url: str, delay: float, headers: dict | None = None, max_retries: int = 3) -> requests.Response | None: ...
