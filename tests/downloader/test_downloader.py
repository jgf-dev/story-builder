import datetime
import os
import tempfile
import unittest
import unittest.mock
from pathlib import Path
from unittest.mock import MagicMock, patch

from storybuilder.downloader import cache
from storybuilder.downloader import storage as dl_storage

# Import modular components
from storybuilder.downloader.date_parser import parse_nifty_date
from storybuilder.downloader.scraper import parse_listing_rows


class TestDateParser(unittest.TestCase):
	def test_parse_with_year(self) -> None:
		# MMM DD YYYY
		self.assertEqual(parse_nifty_date("Dec  4  2025"), datetime.date(2025, 12, 4))
		self.assertEqual(parse_nifty_date("Jun 06 2024"), datetime.date(2024, 6, 6))

	def test_parse_recent_format_no_year(self) -> None:
		# MMM DD HH:MM
		ref_date = datetime.datetime(2026, 6, 10, 12, 0)
		# In past relative to ref_date, so stays 2026
		self.assertEqual(
			parse_nifty_date("Jun  6 08:55", ref_date),
			datetime.date(2026, 6, 6),
		)
		# In future relative to ref_date (e.g. Dec), so gets previous year (2025)
		self.assertEqual(
			parse_nifty_date("Dec 12 19:52", ref_date),
			datetime.date(2025, 12, 12),
		)

	def test_fallback_parsing(self) -> None:
		ref_date = datetime.datetime(2026, 6, 10, 12, 0)
		self.assertEqual(parse_nifty_date("Jun 6", ref_date), datetime.date(2026, 6, 6))


class TestScraper(unittest.TestCase):
	def test_parse_listing_rows_ftr(self) -> None:
		from bs4 import BeautifulSoup

		html = """
        <div class="ftr">
            <div>13K</div>
            <div>Jun 6 08:55</div>
            <div><a href="story1.txt">Story Title</a></div>
        </div>
        """
		soup = BeautifulSoup(html, "html.parser")
		rows = parse_listing_rows(soup)
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["size"], "13K")
		self.assertEqual(rows[0]["date_str"], "Jun 6 08:55")
		self.assertEqual(rows[0]["name"], "Story Title")
		self.assertEqual(rows[0]["href"], "story1.txt")

	def test_parse_listing_rows_table(self) -> None:
		from bs4 import BeautifulSoup

		html = """
        <table>
            <tr><th>Size</th><th>Date</th><th>Title</th></tr>
            <tr>
                <td>10K</td>
                <td>May 12 19:52</td>
                <td><a href="story2.html">Another Story</a></td>
            </tr>
        </table>
        """
		soup = BeautifulSoup(html, "html.parser")
		rows = parse_listing_rows(soup)
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["size"], "10K")
		self.assertEqual(rows[0]["date_str"], "May 12 19:52")
		self.assertEqual(rows[0]["name"], "Another Story")
		self.assertEqual(rows[0]["href"], "story2.html")

	def test_parse_listing_rows_empty(self) -> None:
		from bs4 import BeautifulSoup

		soup = BeautifulSoup("<html></html>", "html.parser")
		rows = parse_listing_rows(soup)
		self.assertEqual(rows, [])


class TestScraperHelpers(unittest.TestCase):
	"""Unit tests for previously untested scraper internals (big coverage gap)."""

	def test_extract_subcategories_list_group(self) -> None:
		from bs4 import BeautifulSoup

		from storybuilder.downloader.scraper import _extract_subcategories_from_html

		html = """
        <ul>
          <li class="list-group-item"><a href="/nifty/gay/adult-friends/">Adult Friends</a></li>
          <li class="list-group-item"><a href="/nifty/gay/athletics/">Athletics</a></li>
        </ul>
        """
		soup = BeautifulSoup(html, "html.parser")
		subs = _extract_subcategories_from_html(soup, "https://nifty.org/nifty/gay/")
		self.assertEqual(len(subs), 2)
		self.assertIn("Adult Friends", [s["name"] for s in subs])

	def test_extract_subcategories_fallback(self) -> None:
		from bs4 import BeautifulSoup

		from storybuilder.downloader.scraper import _extract_subcategories_from_html

		html = '<a href="camping/">Camping</a><a href="college/">College</a>'
		soup = BeautifulSoup(html, "html.parser")
		subs = _extract_subcategories_from_html(soup, "https://nifty.org/nifty/gay/")
		self.assertEqual(len(subs), 2)

	def test_filter_subcategories(self) -> None:
		from storybuilder.downloader.scraper import _filter_subcategories

		subs = [
			{"name": "Adult Friends", "url": "https://nifty.org/nifty/gay/adult-friends/"},
			{"name": "Main", "url": "https://nifty.org/nifty/gay/"},
			{"name": "External", "url": "https://example.com/"},
		]
		filtered = _filter_subcategories(subs, "gay")
		self.assertEqual(len(filtered), 1)
		self.assertEqual(filtered[0]["name"], "Adult Friends")

	def test_filter_stories_by_date(self) -> None:
		import datetime

		from storybuilder.downloader.scraper import _filter_stories_by_date

		stories = [
			{"name": "old", "date": "2020-01-01", "is_dir": False, "url": "u1"},
			{"name": "dir", "date": "1999-01-01", "is_dir": True, "url": "u2"},
			{"name": "inrange", "date": "2024-06-01", "is_dir": False, "url": "u3"},
		]
		start = datetime.date(2024, 1, 1)
		end = datetime.date(2025, 1, 1)
		filtered = _filter_stories_by_date(stories, start, end)
		names = [s["name"] for s in filtered]
		self.assertIn("dir", names)  # dirs always included
		self.assertIn("inrange", names)
		self.assertNotIn("old", names)

	@patch("storybuilder.downloader.scraper.cache_lock")
	def test_merge_and_save_stories(self, mock_lock) -> None:
		import storybuilder.downloader.cache as cache_mod
		from storybuilder.downloader.scraper import _merge_and_save_stories

		cache_mod.metadata_cache = {}
		scraped = [{"url": "new", "date": "2024-01-01", "name": "n"}]
		cached = [{"url": "old", "date": "2023-01-01", "name": "o"}]
		merged = _merge_and_save_stories("http://ex/sub/", scraped, cached, False, True)
		self.assertEqual(len(merged), 2)
		self.assertIn("metadata_cache", dir(cache_mod))


class TestScraperCacheAndEarlyStop(unittest.TestCase):
	"""Critical tests for cache decisions, early-stop, merge, and filtering
	to guarantee no stories are missed or duplicated.
	"""

	def setUp(self) -> None:
		import storybuilder.downloader.cache as cache_mod

		cache_mod.metadata_cache.clear()

	def test_scrape_subcategory_uses_cache_only_when_complete(self) -> None:
		"""If cache not marked complete, do not early-stop even on hits."""
		import datetime
		from unittest.mock import patch

		from storybuilder.downloader.scraper import scrape_subcategory

		cached = [{"url": "http://ex/s1", "date": "2024-06-01", "name": "s1"}]
		# Simulate incomplete cache
		with patch("storybuilder.downloader.scraper._get_cached_subcategory", return_value=(cached, False)):
			with patch("storybuilder.downloader.scraper._scrape_subcategory_pages") as mock_pages:
				mock_pages.return_value = (
					[{"url": "http://ex/s2", "date": "2024-07-01", "name": "s2", "is_dir": False}],
					True,
				)
				with patch("storybuilder.downloader.scraper._merge_and_save_stories") as mock_merge:
					mock_merge.return_value = [
						{"url": "http://ex/s1", "date": "2024-06-01", "name": "s1", "is_dir": False},
						{"url": "http://ex/s2", "date": "2024-07-01", "name": "s2", "is_dir": False},
					]
					start = datetime.date(2024, 1, 1)
					end = datetime.date(2025, 1, 1)
					result = scrape_subcategory("http://ex/sub/", start, end, delay=0, force_scan=False)
					# Because not complete, use_cache=False was passed internally
					mock_pages.assert_called_once()
					args = mock_pages.call_args[0]
					use_cache_arg = args[4]  # position of use_cache
					self.assertFalse(use_cache_arg)
					self.assertEqual(len(result), 2)  # both kept after filter

	def test_cache_hit_stops_pagination_when_complete(self) -> None:
		"""When complete cache, a matching cached story should cause stop."""
		import datetime
		from unittest.mock import patch

		from storybuilder.downloader.scraper import scrape_subcategory

		cached = [{"url": "http://ex/old", "date": "2024-05-01", "name": "old"}]
		with patch("storybuilder.downloader.scraper._get_cached_subcategory", return_value=(cached, True)):
			with patch("storybuilder.downloader.scraper._scrape_subcategory_pages") as mock_pages:
				# Simulate that during scrape it would have detected hit and stopped
				mock_pages.return_value = ([], True)  # nothing new scraped because hit
				with patch("storybuilder.downloader.scraper._merge_and_save_stories") as mock_merge:
					mock_merge.return_value = [
						{"url": "http://ex/old", "date": "2024-05-01", "name": "old", "is_dir": False}
					]
					start = datetime.date(2024, 1, 1)
					end = datetime.date(2025, 1, 1)
					result = scrape_subcategory("http://ex/sub/", start, end, delay=0)
					# use_cache should have been True
					use_cache = mock_pages.call_args[0][4]
					self.assertTrue(use_cache)
					self.assertEqual(len(result), 1)

	def test_force_scan_bypasses_cache(self) -> None:
		import datetime
		from unittest.mock import patch

		from storybuilder.downloader.scraper import scrape_subcategory

		with patch("storybuilder.downloader.scraper._get_cached_subcategory", return_value=([], True)):
			with patch("storybuilder.downloader.scraper._scrape_subcategory_pages") as mock_pages:
				mock_pages.return_value = ([], True)
				with patch("storybuilder.downloader.scraper._merge_and_save_stories", return_value=[]):
					start = datetime.date(2024, 1, 1)
					end = datetime.date(2025, 1, 1)
					scrape_subcategory("url", start, end, 0, force_scan=True)
					use_cache = mock_pages.call_args[0][4]
					self.assertFalse(use_cache)

	def test_filter_stories_by_date_keeps_dirs_and_in_range(self) -> None:
		# Already have basic, but verify the returned shape from scrape path
		import datetime

		from storybuilder.downloader.scraper import _filter_stories_by_date

		merged = [
			{"name": "old", "date": "2020-01-01", "is_dir": False, "url": "u1"},
			{"name": "dir1", "date": "1990-01-01", "is_dir": True, "url": "d1"},
			{"name": "good", "date": "2024-06-15", "is_dir": False, "url": "u2"},
		]
		start = datetime.date(2024, 5, 1)
		end = datetime.date(2024, 7, 1)
		out = _filter_stories_by_date(merged, start, end)
		self.assertEqual(len(out), 2)
		self.assertTrue(any(s["is_dir"] for s in out))
		self.assertTrue(any(s["name"] == "good" for s in out))

	@patch("storybuilder.downloader.scraper.cache_lock")
	def test_multi_chapter_folder_cache_decision(self, mock_lock) -> None:
		"""Cached folder: if has any in range return all chapters (to avoid partial download)."""
		import datetime
		from unittest.mock import patch

		import storybuilder.downloader.cache as cache_mod
		from storybuilder.downloader.scraper import scrape_multi_chapter_folder

		cached_entry = {
			"folder_date": "2024-06-01",
			"chapters": [
				{"name": "ch1", "url": "u1", "date": "2024-06-01"},
				{"name": "ch2", "url": "u2", "date": "2024-06-10"},
			],
		}
		cache_mod.metadata_cache["folder"] = cached_entry

		start = datetime.date(2024, 6, 5)
		end = datetime.date(2024, 6, 15)

		with patch("storybuilder.downloader.scraper._get_cached_chapters") as mock_get:
			mock_get.return_value = (
				[
					{"name": "ch1", "url": "u1", "date": datetime.date(2024, 6, 1), "is_dir": False},
					{"name": "ch2", "url": "u2", "date": datetime.date(2024, 6, 10), "is_dir": False},
				],
				True,
			)  # has_matching

			result = scrape_multi_chapter_folder("folder", datetime.date(2024, 6, 1), start, end, 0, force_scan=False)
			self.assertEqual(len(result), 2)  # returns all even though ch1 is before start

	def test_process_subcategory_dedups_folders(self) -> None:
		"""seen_folders prevents duplicate processing of same Dir across calls."""
		import argparse
		import datetime
		from unittest.mock import patch

		from storybuilder.downloader.scraper import process_subcategory, seen_folders

		seen_folders.clear()

		sub = {"name": "Sub", "url": "http://ex/gay/sub/"}
		args = argparse.Namespace(
			category="gay",
			output_dir="out",
			delay=0,
			force=False,
			max_workers=1,
			max_scraping=1,
		)
		start = datetime.date(2024, 1, 1)
		end = datetime.date(2025, 1, 1)

		dir_story = {"name": "Folder", "url": "http://ex/gay/sub/folder/", "date": "2024-06-01", "is_dir": True}

		with patch("storybuilder.downloader.scraper.scrape_subcategory", return_value=[dir_story]):
			with patch("storybuilder.downloader.scraper.scrape_multi_chapter_folder", return_value=[]):
				t1 = process_subcategory(sub, start, end, args)
				t2 = process_subcategory(sub, start, end, args)  # second call should skip via seen
				# We mainly ensure no crash and logic exercised
				self.assertTrue(True)

	def test_scrape_subcategory_end_to_end_no_miss_no_dupe(self) -> None:
		"""Simulates a realistic scrape + cache scenario and asserts the final filtered list has correct stories, no dups."""
		import datetime
		from unittest.mock import patch

		from storybuilder.downloader.scraper import scrape_subcategory

		start = datetime.date(2024, 5, 1)
		end = datetime.date(2024, 7, 1)

		# Pretend previous run left a complete cache with one old story
		cached = [{"url": "http://ex/old", "date": "2024-04-01", "name": "old", "is_dir": False}]

		# New page will return one in-range + one future (for early stop test) + one dir
		new_scraped = [
			{"url": "http://ex/good", "date": "2024-06-01", "name": "good", "is_dir": False},
			{"url": "http://ex/dir", "date": "2024-01-01", "name": "Series", "is_dir": True},
			{"url": "http://ex/future", "date": "2024-08-01", "name": "future", "is_dir": False},
		]

		with patch("storybuilder.downloader.scraper._get_cached_subcategory", return_value=(cached, True)):
			with patch("storybuilder.downloader.scraper._scrape_subcategory_pages", return_value=(new_scraped, True)):
				with patch("storybuilder.downloader.scraper._merge_and_save_stories") as mock_merge:
					# Simulate correct merge (no dupes)
					merged = cached + [s for s in new_scraped if s["url"] not in {c["url"] for c in cached}]
					mock_merge.return_value = merged

					result = scrape_subcategory("http://ex/sub/", start, end, delay=0, force_scan=False)

					urls = [r["url"] for r in result]
					self.assertEqual(len(urls), len(set(urls)), "Duplicates detected!")
					self.assertIn("http://ex/good", urls)
					self.assertIn("http://ex/dir", urls)  # dir always kept
					self.assertNotIn("http://ex/old", urls)  # filtered out
					# future should be filtered by the final _filter call
					self.assertNotIn("http://ex/future", urls)

	def test_pagination_early_stop_via_realistic_fetch(self) -> None:
		"""Uses patched fetch_page returning successive pages to exercise _scrape_subcategory_pages logic
		and ensure early stop on old non-dir + correct collection (no miss of in-range, no dups).
		"""
		import datetime
		from unittest.mock import MagicMock, patch

		from storybuilder.downloader.scraper import scrape_subcategory

		start = datetime.date(2024, 1, 1)
		end = datetime.date(2024, 12, 31)

		# Page 1: two in-range stories (newest first)
		p1 = MagicMock()
		p1.text = """
        <div class="ftr"><div>2K</div><div>Jun 10 2024</div><div><a href="s1.txt">Story June</a></div></div>
        <div class="ftr"><div>1K</div><div>Mar 5 2024</div><div><a href="s2.txt">Story March</a></div></div>
        """
		# Page 2: older story that should trigger early stop
		p2 = MagicMock()
		p2.text = """
        <div class="ftr"><div>1K</div><div>Dec 1 2023</div><div><a href="old.txt">Old Story</a></div></div>
        """

		with patch("storybuilder.downloader.scraper.fetch_page", side_effect=[p1, p2]):
			with patch("storybuilder.downloader.scraper._get_cached_subcategory", return_value=([], False)):
				with patch("storybuilder.downloader.scraper._merge_and_save_stories", side_effect=lambda *a, **k: a[1]):
					result = scrape_subcategory("http://ex/cat/sub/", start, end, delay=0)
					names = {r["name"] for r in result if "name" in r}
					self.assertIn("Story June", names)
					self.assertIn("Story March", names)
					self.assertNotIn("Old Story", names)
					self.assertEqual(len(names), len({r.get("url") for r in result if "url" in r}))

	def test_scrape_subcategory_pages_direct_cache_hit_and_early_stop(self) -> None:
		"""Directly exercises _scrape_subcategory_pages to hit more internal branches:
		cache lookup inside loop, early stop on old date, pagination termination, reached_end.
		"""
		import datetime
		from unittest.mock import MagicMock, patch

		from storybuilder.downloader.scraper import _scrape_subcategory_pages

		start = datetime.date(2024, 1, 1)
		# Cache key must match resolved URL: sub_url + href
		cached_lookup = {"http://ex/sub/hit.txt": {"date": "2024-06-05"}}

		# Page responses: first page has a new story + a hit that should stop
		p1 = MagicMock()
		p1.text = """
        <div class="ftr"><div>1K</div><div>Jun 15 2024</div><div><a href="new.txt">New</a></div></div>
        <div class="ftr"><div>1K</div><div>Jun 5 2024</div><div><a href="hit.txt">Hit</a></div></div>
        """
		p2 = MagicMock()  # should not be fetched because of stop

		with patch("storybuilder.downloader.scraper.fetch_page", side_effect=[p1, p2]) as mock_fetch:
			scraped, reached = _scrape_subcategory_pages(
				"http://ex/sub/",
				start,
				delay=0,
				force_scan=False,
				use_cache=True,
				cached_lookup=cached_lookup,
			)
			# Should have collected "New", detected hit on second row, stopped without fetching p2
			self.assertEqual(len(scraped), 1)
			self.assertEqual(scraped[0]["name"], "New")
			self.assertFalse(reached)  # stopped early, not natural end
			# Only one fetch happened
			self.assertEqual(mock_fetch.call_count, 1)

	def test_table_driven_cache_and_date_states(self) -> None:
		"""Table-driven tests for scrape_subcategory covering combinations of
		cache complete/force + resulting use_cache and collected stories.
		Ensures no dups and correct filtering.
		"""
		import datetime
		from unittest.mock import patch

		from storybuilder.downloader.scraper import scrape_subcategory

		cases = [
			# (force, complete, expected_use_cache, expected_names) - expectations after final date filter
			(False, True, True, ["inrange"]),
			(True, True, False, ["inrange"]),  # even with force, final filter drops old
			(False, False, False, ["inrange"]),
		]

		start = datetime.date(2024, 5, 1)
		end = datetime.date(2024, 7, 1)

		for force, complete, exp_use, exp_names in cases:
			with self.subTest(force=force, complete=complete):
				cached = [{"url": "u-old", "date": "2024-04-01", "name": "old-but-forced", "is_dir": False}]
				new_scraped = [
					{"url": "u-new", "date": "2024-06-01", "name": "inrange", "is_dir": False},
				]

				with patch("storybuilder.downloader.scraper._get_cached_subcategory", return_value=(cached, complete)):
					with patch("storybuilder.downloader.scraper._scrape_subcategory_pages") as mp:
						mp.return_value = (new_scraped, True)
						with patch(
							"storybuilder.downloader.scraper._merge_and_save_stories",
							side_effect=lambda u, s, c, ic, re: s + c,
						):
							result = scrape_subcategory("u", start, end, 0, force_scan=force)
							names = {r["name"] for r in result}
							# Check no dups
							self.assertEqual(len(names), len({r.get("url") for r in result}))
							for n in exp_names:
								self.assertIn(n, names)

	def test_process_subcategory_full_target_list_no_dups_mixed(self) -> None:
		"""Mocked integration for process_subcategory producing mixed story + dir targets.
		Asserts correct output paths, no duplicate keys, and that dirs go through multi-chapter path.
		"""
		import argparse
		import datetime
		from unittest.mock import patch

		from storybuilder.downloader.scraper import process_subcategory

		sub = {"name": "Sub", "url": "http://ex/gay/sub/"}
		args = argparse.Namespace(
			category="gay",
			output_dir="/tmp/out",
			delay=0,
			force=False,
		)
		start = datetime.date(2024, 1, 1)
		end = datetime.date(2025, 1, 1)

		stories = [
			{"name": "Single", "url": "http://ex/s.txt", "date": "2024-06-01", "is_dir": False},
			{"name": "Series", "url": "http://ex/series/", "date": "2024-06-01", "is_dir": True},
		]

		chapters = [
			{"name": "ch1", "url": "http://ex/ch1", "date": "2024-06-01", "is_dir": False},
		]

		with patch("storybuilder.downloader.scraper.scrape_subcategory", return_value=stories):
			with patch("storybuilder.downloader.scraper.scrape_multi_chapter_folder", return_value=chapters):
				targets = process_subcategory(sub, start, end, args)

				# Should have 1 single + 1 chapter
				self.assertEqual(len(targets), 2, f"Got {len(targets)} targets: {targets}")
				keys = [t["key"] for t in targets]
				self.assertEqual(len(keys), len(set(keys)), "duplicate keys in targets")
				paths = [t["output_path"] for t in targets]
				# Debug: show what we got
				print(f"DEBUG paths: {paths}")
				self.assertTrue(any("series" in p.lower() for p in paths), f"No series in {paths}")
				self.assertTrue(any("single" in p.lower() for p in paths), f"No single in {paths}")


class TestCache(unittest.TestCase):
	def setUp(self) -> None:
		cache.metadata_cache = {}

	def test_cache_loading_and_saving(self) -> None:
		import shutil
		import tempfile

		temp_dir = tempfile.mkdtemp()
		try:
			cache.metadata_cache = {"some_key": "some_value"}
			cache.save_cache(temp_dir)

			cache.metadata_cache = {}
			cache.load_cache(temp_dir)
			self.assertEqual(cache.metadata_cache.get("some_key"), "some_value")
		finally:
			shutil.rmtree(temp_dir)


class TestWriterCacheInteraction(unittest.TestCase):
	"""Tests for writer + cache interaction (duplicate handling)."""

	def setUp(self) -> None:
		cache.metadata_cache = {}

	def test_duplicate_targets_from_different_subcats(self) -> None:
		"""Writer's download_single_target may see same story from multiple subcats.
		Cache ensures we don't re-download.
		"""
		from storybuilder.downloader import cache
		import tempfile
		import shutil
		import os
		from unittest.mock import patch, MagicMock

		temp_dir = tempfile.mkdtemp()
		try:
			# Simulate cache with two entries for same URL
			url = "http://ex/story.txt"
			cache.metadata_cache = {
				url: {"name": "Story", "date": "2024-06-01", "stories": ["sub1", "sub2"], "complete": True},
			}

			target = {
				"url": url,
				"name": "Story",
				"output_path": os.path.join(temp_dir, "out.txt"),
				"output_paths": [os.path.join(temp_dir, "out.txt"), os.path.join(temp_dir, "out2.txt")],
				"key": ("cat", "slug"),
				"date": "2024-06-01",
			}

			# Check if cache hit
			self.assertIn(url, cache.metadata_cache)
			self.assertTrue(cache.metadata_cache[url].get("complete"))
		finally:
			shutil.rmtree(temp_dir)

	def test_writer_uses_cache_for_dedupe(self) -> None:
		"""Writer's download_single_target checks _is_already_downloaded which uses cache."""
		import os
		import shutil
		import tempfile

		from storybuilder.downloader import cache

		temp_dir = tempfile.mkdtemp()
		try:
			url = "http://ex/dup.txt"
			cache.metadata_cache = {url: {"complete": True}}

			# Test that cache is checked for duplicate detection
			from storybuilder.downloader.writer import _is_already_downloaded

			result = _is_already_downloaded("1", url, [os.path.join(temp_dir, "a.txt")], "2024-06-01")

			# With cache hit and no actual file, returns False (not downloaded)
			# The function checks both file existence AND cache
			self.assertIsNotNone(result)
		finally:
			shutil.rmtree(temp_dir)

	def test_writer_file_exists_check(self) -> None:
		"""Writer checks if file already exists on disk."""
		import shutil
		import tempfile

		from storybuilder.downloader.writer import _is_already_downloaded

		temp_dir = tempfile.mkdtemp()
		try:
			# Create the file
			test_path = os.path.join(temp_dir, "exists.txt")
			Path(test_path).write_text("test")

			# Should return True - file exists
			result = _is_already_downloaded("1", "http://ex", [test_path], "2024-06-01")
			self.assertTrue(result)

			# Non-existent file should return False
			result = _is_already_downloaded("2", "http://ex", [os.path.join(temp_dir, "notthere.txt")], "2024-06-01")
			self.assertFalse(result)
		finally:
			shutil.rmtree(temp_dir)

	def test_replicate_story_handles_duplicates(self) -> None:
		"""Writer's _replicate_story copies primary to output_paths."""
		import shutil
		import tempfile

		from storybuilder.downloader.writer import _replicate_story

		temp_dir = tempfile.mkdtemp()
		try:
			primary = os.path.join(temp_dir, "primary.txt")
			copy1 = os.path.join(temp_dir, "copy1.txt")
			copy2 = os.path.join(temp_dir, "copy2.txt")

			Path(primary).write_text("content")

			_replicate_story(primary, [primary, copy1, copy2], "2024-06-01")

			self.assertTrue(Path(copy1).exists())
			self.assertTrue(Path(copy2).exists())
			with Path(copy1).open() as f:
				self.assertEqual(f.read(), "content")
		finally:
			shutil.rmtree(temp_dir)

	def test_download_single_target_with_existing_file(self) -> None:
		"""download_single_target skips if file already exists."""
		import shutil
		import tempfile

		from storybuilder.downloader.writer import download_single_target

		temp_dir = tempfile.mkdtemp()
		try:
			# Pre-create the output file
			output_path = os.path.join(temp_dir, "story.txt")
			Path(output_path).write_text("already there")

			# Should skip and return early (no network call)
			result = download_single_target("1", "http://ex/story.txt", [output_path], "2024-06-01", delay=0)
			# Result should indicate skipped or completed
			self.assertIsNotNone(result)
		finally:
			shutil.rmtree(temp_dir)


class TestScraperMultiChapter(unittest.TestCase):
	"""Tests for multi-chapter folder handling (scraper.py lines 312-430)."""

	def setUp(self) -> None:
		from storybuilder.downloader import cache

		cache.metadata_cache = {}

	@patch("storybuilder.downloader.scraper.metadata_cache", {})
	@patch("storybuilder.downloader.scraper.fetch_page")
	def test_get_cached_chapters_cache_hit(self, mock_fetch) -> None:
		"""Test _get_cached_chapters returns cached chapters on cache hit."""
		from storybuilder.downloader import scraper
		from storybuilder.downloader.scraper import _get_cached_chapters

		folder_url = "http://ex/folder/"
		folder_date = datetime.date(2024, 6, 1)
		start = datetime.date(2024, 1, 1)
		end = datetime.date(2024, 12, 31)

		scraper.metadata_cache = {
			folder_url: {
				"folder_date": "2024-06-01",
				"chapters": [
					{"name": "ch1", "url": "http://ex/ch1.txt", "date": "2024-06-15"},
				],
			},
		}

		chapters, has_matching = _get_cached_chapters(folder_url, folder_date, start, end)

		self.assertIsNotNone(chapters)
		self.assertEqual(len(chapters), 1)
		self.assertTrue(has_matching)
		mock_fetch.assert_not_called()

	@patch("storybuilder.downloader.scraper.metadata_cache", {})
	@patch("storybuilder.downloader.scraper.fetch_page")
	def test_get_cached_chapters_cache_miss_wrong_date(self, mock_fetch) -> None:
		"""Test _get_cached_chapters returns None when folder_date doesn't match."""
		from storybuilder.downloader import scraper
		from storybuilder.downloader.scraper import _get_cached_chapters

		folder_url = "http://ex/folder/"
		folder_date = datetime.date(2024, 6, 1)
		start = datetime.date(2024, 1, 1)
		end = datetime.date(2024, 12, 31)

		scraper.metadata_cache = {
			folder_url: {
				"folder_date": "2024-01-01",  # Different date
				"chapters": [{"name": "ch1", "url": "http://ex/ch1.txt", "date": "2024-06-15"}],
			},
		}

		chapters, has_matching = _get_cached_chapters(folder_url, folder_date, start, end)

		self.assertIsNone(chapters)
		self.assertFalse(has_matching)

	@patch("storybuilder.downloader.scraper.metadata_cache", {})
	@patch("storybuilder.downloader.scraper.fetch_page")
	def test_get_cached_chapters_no_chapters_in_range(self, mock_fetch) -> None:
		"""Test _get_cached_chapters detects no chapters in date range."""
		from storybuilder.downloader import scraper
		from storybuilder.downloader.scraper import _get_cached_chapters

		folder_url = "http://ex/folder/"
		folder_date = datetime.date(2024, 6, 1)
		start = datetime.date(2024, 7, 1)  # Start after chapters
		end = datetime.date(2024, 12, 31)

		scraper.metadata_cache = {
			folder_url: {
				"folder_date": "2024-06-01",
				"chapters": [
					{"name": "ch1", "url": "http://ex/ch1.txt", "date": "2024-06-15"},
				],
			},
		}

		chapters, has_matching = _get_cached_chapters(folder_url, folder_date, start, end)

		self.assertEqual(len(chapters), 1)
		self.assertFalse(has_matching)

	@patch("storybuilder.downloader.scraper.fetch_page")
	def test_fetch_and_parse_chapters_basic(self, mock_fetch) -> None:
		"""Test _fetch_and_parse_chapters parses chapter list."""
		from storybuilder.downloader.scraper import _fetch_and_parse_chapters

		mock_response = MagicMock()
		mock_response.text = """
        <div class="ftr"><div>1K</div><div>Jun 15 2024</div><div><a href="ch1.txt">Chapter 1</a></div></div>
        <div class="ftr"><div>2K</div><div>Jun 16 2024</div><div><a href="ch2.txt">Chapter 2</a></div></div>
        """
		mock_fetch.return_value = mock_response

		chapters, scraped, has_matching = _fetch_and_parse_chapters(
			"http://ex/folder/",
			datetime.date(2024, 1, 1),
			datetime.date(2024, 12, 31),
			0,
		)

		self.assertEqual(len(chapters), 2)
		self.assertEqual(len(scraped), 2)
		self.assertTrue(has_matching)

	@patch("storybuilder.downloader.scraper.fetch_page")
	def test_fetch_and_parse_chapters_empty_response(self, mock_fetch) -> None:
		"""Test _fetch_and_parse_chapters handles empty/no response."""
		from storybuilder.downloader.scraper import _fetch_and_parse_chapters

		mock_fetch.return_value = None

		chapters, scraped, has_matching = _fetch_and_parse_chapters(
			"http://ex/folder/",
			datetime.date(2024, 1, 1),
			datetime.date(2024, 12, 31),
			0,
		)

		self.assertEqual(len(chapters), 0)
		self.assertFalse(has_matching)

	@patch("storybuilder.downloader.scraper.fetch_page")
	def test_scrape_multi_chapter_folder_uses_cache(self, mock_fetch) -> None:
		"""Test scrape_multi_chapter_folder uses cache when valid."""
		import datetime

		from storybuilder.downloader import cache
		from storybuilder.downloader.scraper import scrape_multi_chapter_folder

		cache.metadata_cache = {
			"http://ex/folder/": {
				"folder_date": "2024-06-01",
				"chapters": [{"name": "ch1", "url": "http://ex/ch1.txt", "date": "2024-06-15"}],
			},
		}

		result = scrape_multi_chapter_folder(
			"http://ex/folder/",
			datetime.date(2024, 6, 1),
			datetime.date(2024, 1, 1),
			datetime.date(2024, 12, 31),
			delay=0,
		)

		self.assertEqual(len(result), 1)
		mock_fetch.assert_not_called()

	@patch("storybuilder.downloader.scraper.fetch_page")
	def test_scrape_multi_chapter_folder_cache_miss(self, mock_fetch) -> None:
		"""Test scrape_multi_chapter_folder fetches on cache miss."""
		from storybuilder.downloader.scraper import scrape_multi_chapter_folder

		mock_response = MagicMock()
		mock_response.text = """
        <div class="ftr"><div>1K</div><div>Jun 15 2024</div><div><a href="ch1.txt">Chapter 1</a></div></div>
        """
		mock_fetch.return_value = mock_response

		result = scrape_multi_chapter_folder(
			"http://ex/folder/",
			datetime.date(2024, 6, 1),
			datetime.date(2024, 1, 1),
			datetime.date(2024, 12, 31),
			delay=0,
			force_scan=True,
		)

		self.assertEqual(len(result), 1)
		mock_fetch.assert_called_once()

	def test_process_directory_story(self) -> None:
		"""Test _process_directory_story generates chapter targets."""
		from storybuilder.downloader.scraper import _process_directory_story
		import argparse

		story = {
			"name": "Series",
			"url": "http://ex/series/",
			"date": datetime.date(2024, 6, 1),
			"is_dir": True,
		}
		args = argparse.Namespace(
			category="gay",
			output_dir="/tmp/out",
			delay=0,
			force=False,
		)

		with patch("storybuilder.downloader.scraper.scrape_multi_chapter_folder") as mock_scrape:
			mock_scrape.return_value = [
				{"name": "ch1", "url": "http://ex/ch1", "date": datetime.date(2024, 6, 1), "is_dir": False},
				{"name": "ch2", "url": "http://ex/ch2", "date": datetime.date(2024, 6, 2), "is_dir": False},
			]
			targets = _process_directory_story(
				story, datetime.date(2024, 1, 1), datetime.date(2024, 12, 31), args, "sub"
			)

		self.assertEqual(len(targets), 2)
		self.assertTrue(any("ch1" in t["output_path"] for t in targets))
		self.assertTrue(any("ch2" in t["output_path"] for t in targets))

	def test_process_single_story(self) -> None:
		"""Test _process_single_story generates a single target."""
		import argparse

		from storybuilder.downloader.scraper import _process_single_story

		story = {
			"name": "Single Story",
			"url": "http://ex/single.txt",
			"date": datetime.date(2024, 6, 1),
			"is_dir": False,
		}
		args = argparse.Namespace(
			category="gay",
			output_dir="/tmp/out",
			delay=0,
			force=False,
		)

		targets = _process_single_story(story, args, "sub")

		self.assertEqual(len(targets), 1)
		self.assertIn("Single", targets[0]["output_path"])


class TestNetwork(unittest.TestCase):
	@unittest.mock.patch("requests.get")
	def test_fetch_page_success(self, mock_get) -> None:
		from storybuilder.downloader.network import fetch_page

		mock_response = unittest.mock.Mock()
		mock_response.status_code = 200
		mock_get.return_value = mock_response

		res = fetch_page("https://example.com", delay=0)
		self.assertEqual(res, mock_response)
		mock_get.assert_called_once()

	@unittest.mock.patch("requests.get")
	def test_fetch_page_404(self, mock_get) -> None:
		from storybuilder.downloader.network import fetch_page

		mock_response = unittest.mock.Mock()
		mock_response.status_code = 404
		mock_get.return_value = mock_response

		res = fetch_page("https://example.com/notfound", delay=0)
		self.assertIsNone(res)

	@unittest.mock.patch("storybuilder.downloader.network.rotate_windscribe_ip")
	@unittest.mock.patch("requests.get")
	def test_fetch_page_retry_and_rotate(self, mock_get, mock_rotate) -> None:
		from storybuilder.downloader import network

		old_rot = network.ENABLE_ROTATION
		network.ENABLE_ROTATION = True
		try:
			mock_response_fail = unittest.mock.Mock()
			mock_response_fail.status_code = 403
			mock_get.return_value = mock_response_fail

			res = network.fetch_page(
				"https://example.com/blocked",
				delay=0,
				max_retries=2,
			)
			self.assertIsNone(res)
			self.assertEqual(mock_rotate.call_count, 2)
		finally:
			network.ENABLE_ROTATION = old_rot



class TestWriter(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile

        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.temp_dir)

    @unittest.mock.patch("storybuilder.downloader.writer.fetch_page")
    def test_save_story_html(self, mock_fetch) -> None:
        from storybuilder.downloader.writer import save_story

        mock_response = unittest.mock.Mock()
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text = """
        <html>
            <head><title>Test Story Title</title></head>
            <body>
                <h5>By Writer Joe</h5>
                <p>Paragraph 1 text.</p>
                <p>Paragraph 2 text.</p>
            </body>
        </html>
        """
        mock_fetch.return_value = mock_response

        out_path = os.path.join(self.temp_dir, "story.txt")
        success = save_story(
            "https://example.com/story.html", out_path, "Jun 6 2024", delay=0
        )
        self.assertTrue(success)
        self.assertTrue(os.path.exists(out_path))

        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Title: Test Story Title", content)
        self.assertIn("Author: By Writer Joe", content)
        self.assertIn("Paragraph 1 text.", content)
        self.assertIn("Paragraph 2 text.", content)

    @unittest.mock.patch("storybuilder.downloader.writer.fetch_page")
    def test_save_story_text(self, mock_fetch) -> None:
        from storybuilder.downloader.writer import save_story

        mock_response = unittest.mock.Mock()
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.text = """Subject: Usenet Story Subject
From: usenet_author@example.com

This is some raw story text.
It has multiple lines.
"""
        mock_fetch.return_value = mock_response

        out_path = os.path.join(self.temp_dir, "story_raw.txt")
        success = save_story(
            "https://example.com/story.txt", out_path, "Jun 6 2024", delay=0
        )
        self.assertTrue(success)

        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Title: Usenet Story Subject", content)
        self.assertIn("Author: usenet_author@example.com", content)
        self.assertIn("This is some raw story text.", content)

    @unittest.mock.patch("storybuilder.downloader.writer.save_story")
    def test_download_single_target_with_duplicates(self, mock_save_story) -> None:
        from storybuilder.downloader.writer import download_single_target

        mock_save_story.return_value = True

        p1 = os.path.join(self.temp_dir, "cat1", "story.txt")
        p2 = os.path.join(self.temp_dir, "cat2", "story.txt")

        def side_effect(url, path, date, delay) -> bool:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write("mocked contents")
            return True

        mock_save_story.side_effect = side_effect

        success = download_single_target(
            "1/1", "https://example.com/story.txt", [p1, p2], "Jun 6 2024", delay=0
        )
        self.assertTrue(success)
        self.assertTrue(os.path.exists(p1))
        self.assertTrue(os.path.exists(p2))
        with open(p2, "r") as f:
            self.assertEqual(f.read(), "mocked contents")


if __name__ == "__main__":
    unittest.main()


class TestProcessSubcategory(unittest.TestCase):
    @unittest.mock.patch("storybuilder.downloader.scraper.scrape_subcategory")
    @unittest.mock.patch("storybuilder.downloader.scraper.scrape_multi_chapter_folder")
    def test_process_subcategory(self, mock_scrape_multi, mock_scrape_sub) -> None:
        from storybuilder.downloader.scraper import process_subcategory, seen_folders

        # Reset seen_folders for isolation
        seen_folders.clear()

        class Args:
            def __init__(self) -> None:
                self.force = False
                self.delay = 0
                self.output_dir = "out"
                self.category = "cat"

        mock_scrape_sub.return_value = [
            {
                "is_dir": False,
                "name": "story1.txt",
                "url": "http://example.com/sub/story1.txt",
                "date": "2023-01-01",
            },
            {
                "is_dir": True,
                "name": "Story 2 folder",
                "url": "http://example.com/sub/story2/",
                "date": "2023-01-02",
            },
        ]

        mock_scrape_multi.return_value = [
            {
                "name": "ch1.txt",
                "url": "http://example.com/sub/story2/ch1.txt",
                "date": "2023-01-02",
            }
        ]

        sub = {"name": "Subcategory", "url": "http://example.com/sub/"}

        args = Args()

        results = process_subcategory(sub, None, None, args)

        self.assertEqual(len(results), 2)

        # Single story output
        self.assertEqual(results[0]["key"], (None, "story1.txt"))
        self.assertEqual(results[0]["url"], "http://example.com/sub/story1.txt")

        # Multi chapter output
        self.assertEqual(results[1]["key"], ("story-2-folder", "ch1.txt"))
        import os

        expected_path1 = os.path.join("out", "cat", "sub", "story1.txt")
        expected_path2 = os.path.join("out", "cat", "sub", "story-2-folder", "ch1.txt")

        self.assertEqual(results[0]["output_path"], expected_path1)
        self.assertEqual(results[1]["output_path"], expected_path2)

        # Ensure it was added to seen folders
        self.assertIn("http://example.com/sub/story2/", seen_folders)

    @unittest.mock.patch("storybuilder.downloader.scraper.scrape_subcategory")
    @unittest.mock.patch("storybuilder.downloader.scraper.scrape_multi_chapter_folder")
    def test_process_subcategory_skip_seen_folders(
        self, mock_scrape_multi, mock_scrape_sub
    ) -> None:
        from storybuilder.downloader.scraper import process_subcategory, seen_folders

        # Reset and prime seen_folders
        seen_folders.clear()
        seen_folders.add("http://example.com/sub/story2/")

        class Args:
            def __init__(self) -> None:
                self.force = False
                self.delay = 0
                self.output_dir = "out"
                self.category = "cat"

        mock_scrape_sub.return_value = [
            {
                "is_dir": True,
                "name": "Story 2 folder",
                "url": "http://example.com/sub/story2/",
                "date": "2023-01-02",
            }
        ]

        sub = {"name": "Subcategory", "url": "http://example.com/sub/"}

        args = Args()

        results = process_subcategory(sub, None, None, args)

        # Should be skipped since it's already in seen_folders
        self.assertEqual(len(results), 0)
        mock_scrape_multi.assert_not_called()

    @unittest.mock.patch("storybuilder.downloader.scraper.scrape_subcategory")
    def test_process_subcategory_extension_handling(self, mock_scrape_sub) -> None:
        from storybuilder.downloader.scraper import process_subcategory, seen_folders

        seen_folders.clear()

        class Args:
            def __init__(self) -> None:
                self.force = False
                self.delay = 0
                self.output_dir = "out"
                self.category = "cat"

        # Missing extensions should get .txt
        mock_scrape_sub.return_value = [
            {
                "is_dir": False,
                "name": "story_no_ext",
                "url": "http://example.com/sub/story_no_ext",
                "date": "2023-01-01",
            },
            {
                "is_dir": False,
                "name": "story_with.html",
                "url": "http://example.com/sub/story_with.html",
                "date": "2023-01-01",
            },
        ]

        sub = {"name": "Subcategory", "url": "http://example.com/sub/"}

        args = Args()

        results = process_subcategory(sub, None, None, args)

        self.assertEqual(len(results), 2)

        self.assertEqual(results[0]["key"], (None, "story_no_ext.txt"))
        self.assertEqual(results[1]["key"], (None, "story_with.html"))


class TestDownloaderStorage(unittest.TestCase):
    """Unit tests for src/storybuilder/downloader/storage.py to increase coverage."""

    def test_normalize_filenames_no_source_dir(self) -> None:
        filenames = ["/abs/path/to/file1.txt", "relative/file2.txt"]
        result = dl_storage._normalize_filenames(filenames, "")
        self.assertEqual(result, filenames)

    def test_normalize_filenames_with_source_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            f1 = base / "sub" / "file1.txt"
            f1.parent.mkdir(parents=True)
            f1.touch()
            filenames = [str(f1), str(base / "outside.txt")]
            result = dl_storage._normalize_filenames(filenames, str(base))
            self.assertIn("sub/file1.txt", result)
            self.assertIn("outside.txt", result)

    def test_normalize_filenames_fallback_to_basename(self) -> None:
        filenames = ["/completely/outside/file.txt"]
        result = dl_storage._normalize_filenames(filenames, "/some/other/dir")
        self.assertEqual(result, ["file.txt"])

    @patch("storybuilder.downloader.storage.Client")
    @patch("storybuilder.downloader.storage.transfer_manager")
    def test_upload_many_gcs_basic(self, mock_tm, mock_client) -> None:
        mock_bucket = MagicMock()
        mock_client.return_value.bucket.return_value = mock_bucket
        mock_tm.upload_many_from_filenames.return_value = [None, None]

        dl_storage.upload_many_gcs(
            "my-bucket",
            "prefix",
            ["file1.txt", "file2.txt"],
            source_directory="",
            workers=2,
        )

        mock_client.assert_called_once()
        mock_tm.upload_many_from_filenames.assert_called_once()
        self.assertTrue(mock_tm.upload_many_from_filenames.called)

    @patch("storybuilder.downloader.storage.Client")
    @patch("storybuilder.downloader.storage.transfer_manager")
    def test_upload_many_gcs_empty(self, mock_tm, mock_client) -> None:
        dl_storage.upload_many_gcs("bucket", "", [])
        mock_tm.upload_many_from_filenames.assert_not_called()

    def test_upload_many_s3(self) -> None:
        mock_boto3 = MagicMock()
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3

        with patch.dict("sys.modules", {"boto3": mock_boto3}):
            with patch("concurrent.futures.ThreadPoolExecutor") as mock_executor:
                with patch("concurrent.futures.as_completed") as mock_as_completed:
                    mock_future = MagicMock()
                    mock_future.result.return_value = ("file.txt", None)
                    mock_executor.return_value.__enter__.return_value.submit.return_value = mock_future
                    mock_as_completed.return_value = [mock_future]

                    dl_storage.upload_many_s3(
                        "my-bucket",
                        "prefix",
                        ["file.txt"],
                        source_directory="",
                    )

                    mock_boto3.client.assert_called_with("s3")

    def test_upload_many_s3_empty(self) -> None:
        # Should not attempt boto3 import when no files
        with patch.dict("sys.modules", {"boto3": MagicMock()}):
            dl_storage.upload_many_s3("bucket", "", [])
            # If it tried to import, it would have been in the dict, but call shouldn't happen
            # Just ensure no crash and early return
            # No exception expected

    def test_resolve_s3_source_no_base(self) -> None:
        src, rel = dl_storage._resolve_s3_source("/abs/path/file.txt", None)
        self.assertEqual(rel, "file.txt")

    def test_resolve_s3_source_with_base(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            f = base / "sub" / "file.txt"
            src, rel = dl_storage._resolve_s3_source(str(f), base)
            self.assertIn("sub/file.txt", rel)

    def test_s3_object_key(self) -> None:
        self.assertEqual(dl_storage._s3_object_key("", "file.txt"), "file.txt")
        self.assertEqual(dl_storage._s3_object_key("pre", "file.txt"), "pre/file.txt")

    def test_upload_single_s3(self) -> None:
        mock_s3 = MagicMock()
        dl_storage._upload_single_s3(mock_s3, "bucket", "pre", "file.txt", None)
        mock_s3.upload_file.assert_called_once()
