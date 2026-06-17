import unittest
import unittest.mock
import datetime
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to sys.path to enable absolute imports when run directly as a script
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Add tts-prompt-crafter scripts directory to import split_prompts
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".agent/skills/tts-prompt-crafter/scripts"))
import split_prompts

from storybuilder.downloader.date_parser import parse_nifty_date
from storybuilder.downloader.scraper import parse_listing_rows
from storybuilder.downloader import cache
from storybuilder.downloader.writer import save_story, download_single_target
from storybuilder.downloader.db import init_db, insert_story, optimize_fts, close_db, get_conn, SCHEMA, INDEXES
from storybuilder.genai.client import parse_speech_config


class TestDateParser(unittest.TestCase):
    def test_parse_with_year(self):
        # MMM DD YYYY
        self.assertEqual(parse_nifty_date("Dec  4  2025"), datetime.date(2025, 12, 4))
        self.assertEqual(parse_nifty_date("Jun 06 2024"), datetime.date(2024, 6, 6))

    def test_parse_recent_format_no_year(self):
        # MMM DD HH:MM
        ref_date = datetime.datetime(2026, 6, 10, 12, 0)
        # In past relative to ref_date, so stays 2026
        self.assertEqual(parse_nifty_date("Jun  6 08:55", ref_date), datetime.date(2026, 6, 6))
        # In future relative to ref_date (e.g. Dec), so gets previous year (2025)
        self.assertEqual(parse_nifty_date("Dec 12 19:52", ref_date), datetime.date(2025, 12, 12))

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

            res = network.fetch_page("https://example.com/blocked", delay=0, max_retries=2)
            self.assertIsNone(res)
            self.assertEqual(mock_rotate.call_count, 2)
        finally:
            network.ENABLE_ROTATION = old_rot

class TestDBIntegration(unittest.TestCase):
    """Tests for the new DB layer, specifically around downloader integration."""
    def setUp(self):
        # Use a temporary database for tests
        self.db_path = "/tmp/test_downloader_integration.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        init_db(self.db_path)
        # Ensure download simulation uses the test DB
        self.original_db_path = None
        try:
            # Monkey patch cli.parse_args to return our test DB path
            self.patcher = unittest.mock.patch('storybuilder.downloader.cli.argparse.ArgumentParser.parse_args')
            self.mock_parse_args = self.patcher.start()
            self.mock_parse_args.return_value = unittest.mock.Mock(
                db='/tmp/test_downloader_integration.db',
                category='gay', start_date='2010-01-01',
                end_date='2015-12-31', output_dir='nifty_stories',
                delay=0.01, socks5_proxy="", rotate_on_refusal=True,
                max_workers=1, max_scraping=1, force=False
            )
            # Monkey patch the writer's save_story to bypass network fetch
            self.patcher_writer = unittest.mock.patch('storybuilder.downloader.writer.save_story')
            self.mock_save_story = self.patcher_writer.start()
            # Monkey patch db.init_db to ensure it uses the test DB path
            self.patcher_db = unittest.mock.patch('storybuilder.downloader.db.init_db', return_value=get_conn())
            self.mock_init_db = self.patcher_db.start()

            # Monkey patch scraper functions to avoid hitting network/Nifty site during tests
            self.patcher_get_subcats = unittest.mock.patch('storybuilder.downloader.cli.get_subcategories')
            self.mock_get_subcategories = self.patcher_get_subcats.start()
            self.mock_get_subcategories.return_value = ['mock-subcat']

            self.patcher_proc_subcat = unittest.mock.patch('storybuilder.downloader.cli.process_subcategory')
            self.mock_process_subcategory = self.patcher_proc_subcat.start()
            self.mock_process_subcategory.return_value = [{
                'key': 'test-story',
                'url': 'https://example.com/test-story.html',
                'output_path': '/tmp/test_downloader_integration/gay/mock-subcat/test-story.txt',
                'date': datetime.date(2026, 6, 12)
            }]

            # Monkey patch upload_many to avoid hitting GCS during unit test
            self.patcher_upload = unittest.mock.patch('storybuilder.downloader.cli.upload_many')
            self.mock_upload = self.patcher_upload.start()
        except Exception as e:
            self.fail(f"Error setting up mocks: {e}")

    def tearDown(self):
        # Clean up mocks and temp DB
        self.patcher.stop()
        self.patcher_writer.stop()
        self.patcher_db.stop()
        self.patcher_get_subcats.stop()
        self.patcher_proc_subcat.stop()
        self.patcher_upload.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        close_db()

    def test_downloader_integration_saves_to_db(self):
        """Verify that downloader saves stories to the specified DB."""
        from storybuilder.downloader import cli
        from storybuilder.downloader.writer import save_story # Import necessary for side effect

        # Mock save_story to simulate successful download and return metadata
        def mock_save(url, output_path, story_date, delay):
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"Mock content for {output_path}")
            # Insert into SQLite database to verify integration
            if get_conn() is not None:
                insert_story(
                    output_path=output_path,
                    title='Test Story',
                    author='Test Author',
                    story_date=story_date,
                    url=url,
                    content='Mock content',
                )
            return True # Simulate success

        self.mock_save_story.side_effect = mock_save

        # Simulate the downloader's main logic
        try:
            # Call main. This will trigger parse_args, init_db, scraping, and download calls
            cli.main()
        except SystemExit:
            # Ignore SystemExit which might be raised by argparse if args are invalid etc.
            pass

        # Verify that stories were inserted into the DB
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        self.assertIsNotNone(conn)
        count = conn.execute("SELECT COUNT(*) FROM stories").fetchone()[0]
        self.assertGreater(count, 0, "No stories were inserted into the database.")

        # Check a specific inserted record
        row = conn.execute("SELECT * FROM stories WHERE path LIKE ?", ('%test-story.txt',)).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row['title'], 'Test Story')
        self.assertEqual(row['author_name'], 'Test Author')
        self.assertEqual(row['publication_date'], '2026-06-12')
        conn.close()

class TestGenAIClient(unittest.TestCase):
    def test_parse_speech_config_max_two_voices(self):
        # It should ignore any voices beyond the first two
        markdown_content = """
        ### DIRECTOR'S NOTES
        Style:
        - Speaker1 (Voice: VoiceA): ...
        - Speaker2 (Voice: VoiceB): ...
        - Speaker3 (Voice: VoiceC): ...
        """
        config = parse_speech_config(markdown_content)
        self.assertEqual(len(config), 2)
        self.assertEqual(config[0]["speaker"], "Speaker1")
        self.assertEqual(config[0]["voice"], "VoiceA")
        self.assertEqual(config[1]["speaker"], "Speaker2")
        self.assertEqual(config[1]["voice"], "VoiceB")

    def test_parse_speech_config_multi_speaker(self):
        markdown_content = """
        ### DIRECTOR'S NOTES
        Style:
        - Jace (Voice: Algenib): 27-year-old.
        - Levi (Voice: Zubenelgenubi): 20-year-old.
        """
        config = parse_speech_config(markdown_content)
        self.assertEqual(len(config), 2)
        self.assertEqual(config[0]["speaker"], "Jace")
        self.assertEqual(config[0]["voice"], "Algenib")
        self.assertEqual(config[1]["speaker"], "Levi")
        self.assertEqual(config[1]["voice"], "Zubenelgenubi")

    def test_parse_speech_config_no_speakers(self):
        # When no speakers are found, it should fallback to a single generic voice
        markdown_content = """
        ### DIRECTOR'S NOTES
        Style: Just talk normally.
        """
        config = parse_speech_config(markdown_content)
        self.assertEqual(len(config), 1)
        self.assertNotIn("speaker", config[0])
        self.assertEqual(config[0]["voice"], "Kore")

    def test_parse_speech_config_single_speaker(self):
        # A single speaker should be padded with a Dummy speaker to force multi-speaker mode
        markdown_content = """
        ### DIRECTOR'S NOTES
        Style:
        * Narrator (Voice: Kore): The narrator voice.
        """
        config = parse_speech_config(markdown_content)
        self.assertEqual(len(config), 2)
        self.assertEqual(config[0]["speaker"], "Narrator")
        self.assertEqual(config[0]["voice"], "Kore")
        self.assertEqual(config[1]["speaker"], "Dummy")
        self.assertEqual(config[1]["voice"], "Puck")


class TestSplitPrompts(unittest.TestCase):
    def test_split_line_to_sentences(self):
        line = "Jace: No, that's not what I meant. [gasp] I want you here. But are you sure?"
        sentences = split_prompts.split_line_to_sentences(line, "Jace")
        self.assertEqual(len(sentences), 3)
        self.assertEqual(sentences[0], "Jace: No, that's not what I meant.")
        self.assertEqual(sentences[1], "Jace: [gasp] I want you here.")
        self.assertEqual(sentences[2], "Jace: But are you sure?")

    def test_split_line_to_sentences_no_split_in_brackets(self):
        line = "Jace: [sighs, whispering closely. soft pace] I remember everything. And I want you."
        sentences = split_prompts.split_line_to_sentences(line, "Jace")
        # Should split on the period after bracket, not inside bracket
        self.assertEqual(len(sentences), 2)
        self.assertEqual(sentences[0], "Jace: [sighs, whispering closely. soft pace] I remember everything.")
        self.assertEqual(sentences[1], "Jace: And I want you.")

    def test_filter_preamble_speakers(self):
        preamble = """# AUDIO PROFILE: Levi & Jace
### DIRECTOR'S NOTES
Style:
- Jace (Voice: Algenib): Intimate, deep.
- Levi (Voice: Zubenelgenubi): Breathy, yielding.
- Narrator (Voice: Kore): Clear tone.

Pace: Slow pacing.
"""
        filtered = split_prompts.filter_preamble_speakers(preamble, {"Jace", "Levi"})
        self.assertIn("Jace (Voice: Algenib)", filtered)
        self.assertIn("Levi (Voice: Zubenelgenubi)", filtered)
        self.assertNotIn("Narrator (Voice: Kore)", filtered)

    def test_process_files_splitting(self):
        # Setup a temporary directory to test process_files
        temp_dir = tempfile.mkdtemp()
        try:
            scene_content = """# AUDIO PROFILE: Test
### DIRECTOR'S NOTES
Style:
- Jace (Voice: Algenib): Intimate, deep.
- Levi (Voice: Enceladus): Breathy, yielding.
- Narrator (Voice: Kore): Clear tone.

Pace: Slow.

#### TRANSCRIPT
Jace: First line.
Levi: Second line.
Narrator: Third line introduces a third speaker.
Jace: Fourth line.
"""
            scene_file = os.path.join(temp_dir, "01-scene1.md")
            with open(scene_file, "w") as f:
                f.write(scene_content)

            split_prompts.process_files(temp_dir)

            # Check that scene file was archived
            self.assertFalse(os.path.exists(scene_file))
            self.assertTrue(os.path.exists(os.path.join(temp_dir, "archive", "01-scene1.md")))

            # Check output chunk files
            part1_file = os.path.join(temp_dir, "01-part.md")
            part2_file = os.path.join(temp_dir, "02-part.md")

            self.assertTrue(os.path.exists(part1_file))
            self.assertTrue(os.path.exists(part2_file))

            # Verify part1 has only Jace and Levi
            with open(part1_file, "r") as f:
                p1_content = f.read()
            self.assertIn("Jace (Voice: Algenib)", p1_content)
            self.assertIn("Levi (Voice: Enceladus)", p1_content)
            self.assertNotIn("Narrator (Voice: Kore)", p1_content)
            self.assertIn("Jace: First line.", p1_content)
            self.assertIn("Levi: Second line.", p1_content)
            self.assertNotIn("Narrator: Third line", p1_content)

            # Verify part2 has Narrator and Jace
            with open(part2_file, "r") as f:
                p2_content = f.read()
            self.assertIn("Narrator (Voice: Kore)", p2_content)
            self.assertIn("Jace (Voice: Algenib)", p2_content)
            self.assertNotIn("Levi (Voice: Enceladus)", p2_content)
            self.assertIn("Narrator: Third line", p2_content)
            self.assertIn("Jace: Fourth line.", p2_content)

        finally:
            shutil.rmtree(temp_dir)

    def test_adjacent_tags_warning(self):
        """Test that adjacent tags (e.g., [sighs][whispers]) produce a warning but don't crash."""
        temp_dir = tempfile.mkdtemp()
        try:
            scene_content = """# AUDIO PROFILE: Test
### DIRECTOR'S NOTES
Style:
- Jace (Voice: Algenib): Intimate, deep.
- Levi (Voice: Enceladus): Breathy, yielding.

Pace: Slow.

#### TRANSCRIPT
Jace: [sighs][whispers] I missed you.
Levi: [gasp] [adoration] Me too.
"""
            scene_file = os.path.join(temp_dir, "01-scene1.md")
            with open(scene_file, "w") as f:
                f.write(scene_content)

            # Should print a warning but not crash
            split_prompts.process_files(temp_dir)

            # Verify output files were still created
            part1_file = os.path.join(temp_dir, "01-part.md")
            self.assertTrue(os.path.exists(part1_file))

            with open(part1_file, "r") as f:
                content = f.read()
            # The adjacent-tag line should still be in the output
            self.assertIn("[sighs][whispers]", content)

        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
