from _typeshed import Incomplete

from requests.models import Response
import time
import requests

BASE_URL: Literal['https://nifty.org/nifty/'] = "https://nifty.org/nifty/"
PROXIES: None = None
ENABLE_ROTATION: bool = False


def safe_print(*args: Incomplete, **kwargs: Incomplete) -> None: ...


def rotate_windscribe_ip() -> bool: ...


def fetch_page(url: Incomplete, delay: Incomplete, headers: Incomplete = None, max_retries: int = 3) -> Response | None: ...
