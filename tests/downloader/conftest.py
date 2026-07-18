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

Reset this global state before and after every test to keep tests isolated
regardless of their own cleanup.
"""

from collections.abc import Iterator

import pytest

from storybuilder.downloader import db, scraper


def _reset_downloader_global_state() -> None:
    db.close_db()
    scraper.seen_folders.clear()


@pytest.fixture(autouse=True)
def clean_globals() -> Iterator[None]:
    _reset_downloader_global_state()
    yield
    _reset_downloader_global_state()
