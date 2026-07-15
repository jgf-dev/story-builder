from _typeshed import Incomplete

from datetime import date
import datetime
import os
import re
import threading
import time
import urllib.parse
from bs4 import BeautifulSoup
from .cache import cache_lock
from .cache import metadata_cache
from .cache import safe_print
from .date_parser import parse_nifty_date
from .network import BASE_URL
from .network import fetch_page

seen_folders: Incomplete
seen_folders_lock: LockType


def get_subcategories(category: Incomplete, delay: Incomplete) -> Incomplete: ...


def parse_listing_rows(soup: BeautifulSoup) -> list[dict[str, AttributeValueList | str]]: ...


def scrape_subcategory(sub_url: Incomplete, start_date: Incomplete, end_date: Incomplete, delay: Incomplete, force_scan: Incomplete = False) -> Incomplete: ...


def scrape_multi_chapter_folder(folder_url: Incomplete, folder_date: Incomplete, start_date: Incomplete, end_date: Incomplete, delay: Incomplete, force_scan: Incomplete = False) -> Incomplete: ...


def process_subcategory(sub: Incomplete, start_date: Incomplete, end_date: Incomplete, args: Incomplete) -> Incomplete: ...
