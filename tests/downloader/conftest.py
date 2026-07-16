"""Test isolation fixtures for the downloader test suite.

Several downloader tests mutate module-level globals that then leak into later
tests:

* ``storybuilder.downloader.db.init_db`` sets ``_conn``/``_engine``. If a test
  does not tear this down, ``writer.save_story`` sees an active DB connection,
  skips writing to disk, and fails against a database whose temporary directory
  has already been removed.
* ``storybuilder.downloader.scraper.seen_folders`` accumulates folder URLs, so a
  URL added by one test causes another test to short-circuit with "Skipping
  already scraped folder".

Reset this global state after every test to keep tests isolated regardless of
their own cleanup.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from storybuilder.downloader import db
from storybuilder.downloader import scraper


@pytest.fixture(autouse=True)
def _reset_downloader_global_state() -> Iterator[None]:
    yield
    db.close_db()
    scraper.seen_folders.clear()
