import unittest
import unittest.mock
import datetime
import os

# Import modular components
from storybuilder.downloader.date_parser import parse_nifty_date
from storybuilder.downloader.scraper import parse_listing_rows
from storybuilder.downloader import cache


class TestDateParser(unittest.TestCase):
    def test_parse_with_year(self):
        # MMM DD YYYY
        self.assertEqual(parse_nifty_date("Dec  4  2025"), datetime.date(2025, 12, 4))
        self.assertEqual(parse_nifty_date("Jun 06 2024"), datetime.date(2024, 6, 6))

    def test_parse_recent_format_no_year(self):
        # MMM DD HH:MM
        ref_date = datetime.datetime(2026, 6, 10, 12, 0)
        # In past relative to ref_date, so stays 2026
        self.assertEqual(
            parse_nifty_date("Jun  6 08:55", ref_date), datetime.date(2026, 6, 6)
        )
        # In future relative to ref_date (e.g. Dec), so gets previous year (2025)
        self.assertEqual(
            parse_nifty_date("Dec 12 19:52", ref_date), datetime.date(2025, 12, 12)
        )

    def test_fallback_parsing(self):
        ref_date = datetime.datetime(2026, 6, 10, 12, 0)
        self.assertEqual(parse_nifty_date("Jun 6", ref_date), datetime.date(2026, 6, 6))


class TestScraper(unittest.TestCase):
    def test_parse_listing_rows_ftr(self):
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

    def test_parse_listing_rows_table(self):
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


class TestCache(unittest.TestCase):
    def setUp(self):
        cache.metadata_cache = {}

    def test_cache_loading_and_saving(self):
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()
        try:
            cache.metadata_cache = {"some_key": "some_value"}
            cache.save_cache(temp_dir)

            cache.metadata_cache = {}
            cache.load_cache(temp_dir)
            self.assertEqual(cache.metadata_cache.get("some_key"), "some_value")
        finally:
            shutil.rmtree(temp_dir)


class TestNetwork(unittest.TestCase):
    @unittest.mock.patch("requests.get")
    def test_fetch_page_success(self, mock_get):
        from storybuilder.downloader.network import fetch_page

        mock_response = unittest.mock.Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        res = fetch_page("https://example.com", delay=0)
        self.assertEqual(res, mock_response)
        mock_get.assert_called_once()

    @unittest.mock.patch("requests.get")
    def test_fetch_page_404(self, mock_get):
        from storybuilder.downloader.network import fetch_page

        mock_response = unittest.mock.Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        res = fetch_page("https://example.com/notfound", delay=0)
        self.assertIsNone(res)

    @unittest.mock.patch("storybuilder.downloader.network.rotate_windscribe_ip")
    @unittest.mock.patch("requests.get")
    def test_fetch_page_retry_and_rotate(self, mock_get, mock_rotate):
        from storybuilder.downloader import network

        old_rot = network.ENABLE_ROTATION
        network.ENABLE_ROTATION = True
        try:
            mock_response_fail = unittest.mock.Mock()
            mock_response_fail.status_code = 403
            mock_get.return_value = mock_response_fail

            res = network.fetch_page(
                "https://example.com/blocked", delay=0, max_retries=2
            )
            self.assertIsNone(res)
            self.assertEqual(mock_rotate.call_count, 2)
        finally:
            network.ENABLE_ROTATION = old_rot


class TestWriter(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    @unittest.mock.patch("storybuilder.downloader.writer.fetch_page")
    def test_save_story_html(self, mock_fetch):
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
    def test_save_story_text(self, mock_fetch):
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
    def test_download_single_target_with_duplicates(self, mock_save_story):
        from storybuilder.downloader.writer import download_single_target

        mock_save_story.return_value = True

        p1 = os.path.join(self.temp_dir, "cat1", "story.txt")
        p2 = os.path.join(self.temp_dir, "cat2", "story.txt")

        def side_effect(url, path, date, delay):
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
    def test_process_subcategory(self, mock_scrape_multi, mock_scrape_sub):
        from storybuilder.downloader.scraper import process_subcategory, seen_folders

        # Reset seen_folders for isolation
        seen_folders.clear()

        class Args:
            def __init__(self):
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
    ):
        from storybuilder.downloader.scraper import process_subcategory, seen_folders

        # Reset and prime seen_folders
        seen_folders.clear()
        seen_folders.add("http://example.com/sub/story2/")

        class Args:
            def __init__(self):
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
    def test_process_subcategory_extension_handling(self, mock_scrape_sub):
        from storybuilder.downloader.scraper import process_subcategory, seen_folders

        seen_folders.clear()

        class Args:
            def __init__(self):
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
