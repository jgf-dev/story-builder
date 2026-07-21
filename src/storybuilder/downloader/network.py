import time
import requests

# Base URL for the classic Nifty Archive
BASE_URL = "https://nifty.org/nifty/"

# Global proxy and rotation settings
PROXIES: dict[str, str] | None = None
ENABLE_ROTATION: bool = False


def safe_print(*args, **kwargs) -> None:
    # This will be overridden or imported from utils later, but let's import it locally inside the package
    from .cache import safe_print as cache_safe_print

    cache_safe_print(*args, **kwargs)


def rotate_windscribe_ip() -> bool:
    """
    Rotates the IP address using windscribe-cli.
    """
    safe_print("Request refused or blocked. Attempting to rotate Windscribe IP...")
    try:
        import subprocess

        result = subprocess.run(
            ["windscribe-cli", "ip", "rotate"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode == 0:
            safe_print(
                "Successfully rotated IP. Waiting 10 seconds for connection to stabilize...",
            )
            time.sleep(10)
            return True
        safe_print(f"Failed to rotate IP: {result.stdout.strip() or result.stderr.strip()}")
        return False
    except Exception as e:  # pylint: disable=broad-except
        safe_print(f"Error running windscribe-cli ip rotate: {e}")
        return False


def fetch_page(
    url: str,
    delay: float,
    headers: dict | None = None,
    max_retries: int = 3,
) -> requests.Response | None:
    """
    Fetches a URL with retries and custom headers.
    Optionally routes through global proxies and triggers Windscribe IP rotation on refusal.
    """
    if not headers:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, proxies=PROXIES, timeout=15)
            if response.status_code == 200:
                return response
            if response.status_code == 404:
                safe_print(f"Error 404: Not Found - {url}")
                return None
            if response.status_code in {403, 429, 503}:
                safe_print(
                    f"Warning: Fetching {url} returned status code {response.status_code} (Attempt {attempt + 1}/{max_retries})",
                )
                if ENABLE_ROTATION:
                    rotate_windscribe_ip()
            else:
                safe_print(
                    f"Warning: Fetching {url} returned status code {response.status_code} (Attempt {attempt + 1}/{max_retries})",
                )
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            safe_print(
                f"Warning: Connection/Timeout error on attempt {attempt + 1}/{max_retries} for {url}: {e}",
            )
            if ENABLE_ROTATION:
                rotate_windscribe_ip()
        except Exception as e:  # pylint: disable=broad-except
            safe_print(
                f"Warning: Unexpected error on attempt {attempt + 1}/{max_retries} for {url}: {e}",
            )

        if attempt < max_retries - 1:
            time.sleep(delay * (attempt + 1))

    safe_print(f"Failed to fetch {url} after {max_retries} attempts.")
    return None
