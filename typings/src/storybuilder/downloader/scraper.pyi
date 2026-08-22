from _typeshed import Incomplete

import datetime
import os
import re
import threading
import time
import urllib.parse
from datetime import date
from bs4 import BeautifulSoup
from .cache import cache_lock, metadata_cache, safe_print
from .date_parser import parse_nifty_date
from .network import BASE_URL, fetch_page

seen_folders: Incomplete
seen_folders_lock: LockType


def get_subcategories(category: Incomplete, delay: Incomplete) -> Incomplete: ...


def parse_listing_rows(soup: BeautifulSoup) -> list[dict[str, str]]: ...


def scrape_subcategory(sub_url: Incomplete, start_date: Incomplete, end_date: Incomplete, delay: Incomplete, force_scan: Incomplete = False) -> Incomplete: ...


def scrape_multi_chapter_folder(folder_url: Incomplete, folder_date: Incomplete, start_date: Incomplete, end_date: Incomplete, delay: Incomplete, force_scan: Incomplete = False) -> Incomplete: ...


def process_subcategory(sub: Incomplete, start_date: Incomplete, end_date: Incomplete, args: Incomplete) -> Incomplete: ...
