"""Test isolation fixtures for the dashboard test suite.

Dashboard tests call ``storybuilder.downloader.db.init_db`` in ``setUp`` which
sets module-level ``_conn``/``_engine``. If a test does not tear this down, the
stale connection (pointing at an already-removed temp directory) leaks into
later tests.

Reset this global state before and after every test to keep tests isolated
regardless of their own cleanup.
"""

from collections.abc import Iterator

import pytest

from storybuilder.downloader import db


def _reset_downloader_global_state() -> None:
	db.close_db()


@pytest.fixture(autouse=True)
def clean_globals() -> Iterator[None]:
	_reset_downloader_global_state()
	yield
	_reset_downloader_global_state()
