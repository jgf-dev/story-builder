from _typeshed import Incomplete

import os
import pathlib
import re
from bs4 import BeautifulSoup
from . import db
from .cache import safe_print
from .network import fetch_page


def save_story(story_url: Incomplete, output_path: Incomplete, story_date: Incomplete, delay: Incomplete) -> bool: ...


def download_single_target(idx_str: Incomplete, url: Incomplete, output_paths: Incomplete, story_date: Incomplete, delay: Incomplete, force: bool = False) -> bool: ...
