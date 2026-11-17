"""Re-fetch header-less stories from the archive to recover true publication dates.

Stories flagged with the bulk-touch sentinel (``1970-01-01``) whose URLs have
no file extension are served by nifty.org as ``text/plain`` including the
original usenet-style ``Date:``/``From:``/``Subject:`` headers. Re-fetching
them recovers the true publication date (verified against dated sibling
chapters) and replaces the HTML-stripped content with the richer raw text.
"""

import datetime
import logging
import re
import time
from email.utils import parsedate_to_datetime

import requests

from . import db


logger = logging.getLogger(__name__)

_DATE_HEADER_RE = re.compile(r"(?m)^Date:\s+(.+)$")
_SUBJECT_RE = re.compile(r"(?im)^Subject:\s*(.*)$")
_FROM_RE = re.compile(r"(?im)^From:\s*(.*)$")
_TRAILING_EXT_RE = re.compile(r"\.\w{1,5}/?$")

_USER_AGENT = (
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def is_headerless_url(url: str) -> bool:
	"""True if the URL's last path segment carries no file extension.

	Extension-less URLs are served as raw ``text/plain`` (with usenet
	headers) by the archive; ``.html``/``.txt``/``.pdf`` files are served
	as-is and never gained headers.
	"""
	path = url.split("?", 1)[0].rstrip("/")
	last = path.rsplit("/", 1)[-1]
	return not _TRAILING_EXT_RE.search(last)


def _parse_header_date(text: str, min_date: datetime.date, max_date: datetime.date):
	"""Return (date, subject, from_raw) from a raw text story, or None for the date."""
	m = _DATE_HEADER_RE.search(text[:2000])
	if not m:
		return None, None, None
	try:
		dt = parsedate_to_datetime(m.group(1).strip())
	except (TypeError, ValueError):
		return "parse_failed", None, None
	d = dt.date()
	if d < min_date or d > max_date:
		return "out_of_range", None, None
	subject = _SUBJECT_RE.search(text[:2000])
	from_raw = _FROM_RE.search(text[:2000])
	return d, subject.group(1).strip() if subject else None, from_raw.group(1).strip() if from_raw else None


def refetch_headerless_dates(
	delay: float = 1.5,
	limit: "int | None" = None,
	dry_run: bool = False,
	min_date: str = "1980-01-01",
	update_content: bool = True,
) -> "dict[str, int]":
	"""Re-fetch epoch-flagged extension-less stories and restore their true dates.

	For every story with ``publication_date = db.BULK_TOUCH_EPOCH_DATE`` and an
	extension-less URL, fetches the URL (now served as ``text/plain`` with the
	original usenet headers), parses the ``Date:`` header and writes the true
	date back. When ``update_content`` is set, the richer raw text replaces the
	HTML-stripped content (FTS re-indexing happens through the ``stories_au``
	trigger), and ``title``/``author`` are filled from ``Subject:``/``From:``
	when currently Unknown/empty.

	Duplicate rows sharing a URL are fetched once and updated together.
	Rate-limited by ``delay`` seconds between requests. Returns stats:
	candidates, unique_urls, fetched, dated, no_header, parse_failed,
	out_of_range, http_error, rows_updated.
	"""
	conn = db.get_conn()
	stats = {
		"candidates": 0,
		"unique_urls": 0,
		"fetched": 0,
		"dated": 0,
		"no_header": 0,
		"parse_failed": 0,
		"out_of_range": 0,
		"http_error": 0,
		"rows_updated": 0,
	}
	if conn is None:
		return stats

	min_d = datetime.date.fromisoformat(min_date)
	max_d = datetime.date.today()

	rows = conn.execute(
		"SELECT id, url, title, author_name FROM stories WHERE publication_date = ? AND url IS NOT NULL AND url != ''",
		(db.BULK_TOUCH_EPOCH_DATE,),
	).fetchall()
	by_url: "dict[str, list[tuple]]" = {}
	for rid, url, title, author in rows:
		if not is_headerless_url(url):
			continue
		stats["candidates"] += 1
		by_url.setdefault(url, []).append((rid, title, author))
	urls = list(by_url)
	if limit is not None:
		urls = urls[:limit]
	stats["unique_urls"] = len(urls)
	logger.info("refetch: %d candidate rows, %d unique URLs", stats["candidates"], stats["unique_urls"])

	headers = {"User-Agent": _USER_AGENT}
	for i, url in enumerate(urls):
		try:
			resp = requests.get(url, headers=headers, timeout=25)
		except requests.RequestException as e:
			stats["http_error"] += 1
			logger.warning("refetch network error for %s: %s", url, e)
			time.sleep(delay)
			continue
		stats["fetched"] += 1
		if resp.status_code != 200:
			stats["http_error"] += 1
			logger.warning("refetch HTTP %s for %s", resp.status_code, url)
			time.sleep(delay)
			continue

		parsed, subject, from_raw = _parse_header_date(resp.text, min_d, max_d)
		if parsed is None:
			stats["no_header"] += 1
			time.sleep(delay)
			continue
		if parsed == "parse_failed":
			stats["parse_failed"] += 1
			time.sleep(delay)
			continue
		if parsed == "out_of_range":
			stats["out_of_range"] += 1
			time.sleep(delay)
			continue
		stats["dated"] += 1
		new_date = parsed.isoformat()

		if dry_run:
			stats["rows_updated"] += len(by_url[url])
			time.sleep(delay)
			continue

		content = resp.text if update_content else None
		for rid, title, author in by_url[url]:
			new_title = title
			new_author = author
			if subject and title in (None, "", "Unknown"):
				new_title = subject
			if from_raw and author in (None, "", "Unknown"):
				new_author = from_raw
			if content is not None:
				author_name, author_email = db._parse_author(new_author)
				conn.execute(
					"UPDATE stories SET publication_date=?, date_source=?, content=?, char_count=?, word_count=?, "
					"title=COALESCE(?, title), author_name=COALESCE(?, author_name), "
					"author_email=COALESCE(?, author_email) WHERE id=?",
					(
						new_date,
						db.DATE_SOURCE_REFETCH_HEADER,
						content,
						len(content),
						len(content.split()),
						new_title,
						author_name,
						author_email,
						rid,
					),
				)
			else:
				conn.execute(
					"UPDATE stories SET publication_date=?, date_source=? WHERE id=?",
					(new_date, db.DATE_SOURCE_REFETCH_HEADER, rid),
				)
			stats["rows_updated"] += 1
		conn.commit()
		if (i + 1) % 100 == 0:
			logger.info(
				"refetch progress: %d/%d urls, dated=%d, rows_updated=%d, http_error=%d",
				i + 1,
				len(urls),
				stats["dated"],
				stats["rows_updated"],
				stats["http_error"],
			)
		time.sleep(delay)

	logger.info("refetch done: %s", stats)
	return stats
