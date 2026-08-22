from collections.abc import Iterator
import pytest
from storybuilder.downloader import db


@pytest.fixture(autouse=True)
def clean_globals() -> Iterator[None]: ...
