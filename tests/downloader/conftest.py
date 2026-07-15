from collections.abc import Generator

import pytest

from storybuilder.downloader.db import close_db
from storybuilder.downloader.scraper import seen_folders


def _reset_downloader_globals() -> None:
	seen_folders.clear()
	close_db()


@pytest.fixture(autouse=True)
def clean_globals() -> Generator[None, None, None]:
    """Reset downloader global state around each downloader test."""
    _reset_downloader_globals()
    yield
    _reset_downloader_globals()
