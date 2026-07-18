import unittest
from unittest.mock import patch, MagicMock
import argparse

from storybuilder.downloader.cli import _setup_network
from storybuilder.downloader import network


class TestCLI(unittest.TestCase):
    def setUp(self) -> None:
        # Reset network state before each test
        self.original_proxies = network.PROXIES
        self.original_rotation = network.ENABLE_ROTATION
        network.PROXIES = None
        network.ENABLE_ROTATION = False

    def tearDown(self) -> None:
        # Restore network state after each test
        network.PROXIES = self.original_proxies
        network.ENABLE_ROTATION = self.original_rotation

    def test_setup_network_no_options(self) -> None:
        args = argparse.Namespace(socks5_proxy=None, rotate_on_refusal=False)
        result = _setup_network(args)

        self.assertTrue(result)
        self.assertIsNone(network.PROXIES)
        self.assertFalse(network.ENABLE_ROTATION)

    @patch("builtins.print")
    def test_setup_network_proxy_no_socks_module(self, mock_print) -> None:
        args = argparse.Namespace(
            socks5_proxy="192.168.1.1:1080", rotate_on_refusal=False
        )

        # We need to simulate ImportError when importing 'socks'
        with patch.dict("sys.modules", {"socks": None}):
            result = _setup_network(args)

        self.assertFalse(result)
        self.assertIsNone(network.PROXIES)
        mock_print.assert_any_call(
            "Error: SOCKS proxy support requires the 'pysocks' package."
        )

    def test_setup_network_proxy_without_prefix(self) -> None:
        args = argparse.Namespace(
            socks5_proxy="192.168.1.1:1080", rotate_on_refusal=False
        )

        # Make sure 'socks' module is available
        mock_socks = MagicMock()
        with patch.dict("sys.modules", {"socks": mock_socks}):
            result = _setup_network(args)

        self.assertTrue(result)
        expected_url = "socks5h://192.168.1.1:1080"
        self.assertEqual(network.PROXIES, {"http": expected_url, "https": expected_url})
        self.assertFalse(network.ENABLE_ROTATION)

    def test_setup_network_proxy_with_prefix(self) -> None:
        args = argparse.Namespace(
            socks5_proxy="socks5://192.168.1.1:1080", rotate_on_refusal=False
        )

        mock_socks = MagicMock()
        with patch.dict("sys.modules", {"socks": mock_socks}):
            result = _setup_network(args)

        self.assertTrue(result)
        expected_url = "socks5://192.168.1.1:1080"
        self.assertEqual(network.PROXIES, {"http": expected_url, "https": expected_url})

    def test_setup_network_rotation_enabled(self) -> None:
        args = argparse.Namespace(socks5_proxy=None, rotate_on_refusal=True)

        result = _setup_network(args)

        self.assertTrue(result)
        self.assertIsNone(network.PROXIES)
        self.assertTrue(network.ENABLE_ROTATION)


class TestCLIArgsAndDates(unittest.TestCase):
    """Tests for cli argument parsing and date handling (previously very low coverage)."""

    def test_parse_args_required_category(self) -> None:
        from storybuilder.downloader.cli import _parse_args
        with patch("sys.argv", ["prog", "--category", "gay"]):
            args = _parse_args()
            self.assertEqual(args.category, "gay")
            self.assertEqual(args.start_date, "1990-01-01")

    def test_parse_dates_valid(self) -> None:
        from storybuilder.downloader.cli import _parse_dates
        start, end = _parse_dates("2024-01-01", "2024-12-31")
        self.assertIsNotNone(start)
        self.assertEqual(end.year, 2024)

    def test_parse_dates_invalid_start(self) -> None:
        from storybuilder.downloader.cli import _parse_dates
        start, end = _parse_dates("not-a-date", None)
        self.assertIsNone(start)

    def test_parse_dates_no_end_uses_today(self) -> None:
        from storybuilder.downloader.cli import _parse_dates
        start, end = _parse_dates("2020-01-01", None)
        self.assertIsNotNone(end)
        self.assertGreaterEqual(end, start)

    def test_merge_targets_dedups(self) -> None:
        from storybuilder.downloader.cli import _merge_targets
        targets = {}
        subs = [
            {"key": ("cat", "slug"), "url": "u1", "date": "d", "output_path": "p1"},
            {"key": ("cat", "slug"), "url": "u1", "date": "d", "output_path": "p2"},
        ]
        _merge_targets(targets, subs)
        self.assertEqual(len(targets[("cat", "slug")]["output_paths"]), 2)


class TestCLICacheIntegration(unittest.TestCase):
    """Tests that exercise load_cache / save_cache around the scraping phase in main()."""

    @patch("storybuilder.downloader.cli.load_cache")
    @patch("storybuilder.downloader.cli.save_cache")
    @patch("storybuilder.downloader.cli.get_subcategories")
    @patch("storybuilder.downloader.cli._scrape_subcategories")
    @patch("storybuilder.downloader.cli._upload_to_cloud")
    @patch("storybuilder.downloader.cli._download_stories")
    def test_main_loads_and_saves_cache(self, mock_download, mock_upload, mock_scrape, mock_get_subs, mock_save, mock_load) -> None:
        from storybuilder.downloader.cli import main
        import argparse

        mock_get_subs.return_value = [{"name": "s", "url": "u"}]
        mock_scrape.return_value = {}

        # More direct: patch the functions that are called in the try/finally
        with patch("storybuilder.downloader.cli._parse_args") as pa:
            pa.return_value = argparse.Namespace(
                category="gay", start_date="2024-01-01", end_date=None,
                output_dir="out", delay=0, force=False, socks5_proxy=None,
                rotate_on_refusal=False, max_workers=1, max_scraping=1,
                db="", gcs_bucket="", gcs_prefix="", s3_bucket="", s3_prefix=""
            )
            with patch("storybuilder.downloader.cli._setup_network", return_value=True):
                with patch("storybuilder.downloader.cli._parse_dates", return_value=(__import__("datetime").date(2024,1,1), __import__("datetime").date(2024,12,31))):
                    with patch("storybuilder.downloader.cli._print_config"):
                        main()

        mock_load.assert_called_once_with("out")
        mock_save.assert_called_once_with("out")


class TestCLIEarlyReturns(unittest.TestCase):
    """Tests for early return paths in main()."""

    @patch("storybuilder.downloader.cli._download_stories")
    @patch("storybuilder.downloader.cli._scrape_subcategories")
    @patch("storybuilder.downloader.cli.load_cache")
    @patch("storybuilder.downloader.cli.save_cache")
    @patch("storybuilder.downloader.cli.get_subcategories")
    @patch("storybuilder.downloader.cli._print_config")
    @patch("storybuilder.downloader.cli._parse_dates")
    @patch("storybuilder.downloader.cli._setup_network")
    def test_main_early_return_on_network_failure(self, mock_net, mock_dates, mock_print, mock_subs, mock_save, mock_load, mock_scrape, mock_dl) -> None:
        """main() returns early when _setup_network returns False."""
        from storybuilder.downloader.cli import main
        import argparse

        mock_net.return_value = False  # Network setup fails

        with patch("storybuilder.downloader.cli._parse_args") as pa:
            pa.return_value = argparse.Namespace(
                category="gay", start_date="2024-01-01", end_date=None,
                output_dir="out", delay=0, force=False, socks5_proxy=None,
                rotate_on_refusal=False, max_workers=1, max_scraping=1,
                db="", gcs_bucket="", gcs_prefix="", s3_bucket="", s3_prefix=""
            )
            main()

        # Should not proceed to load cache or scrape
        mock_load.assert_not_called()
        mock_scrape.assert_not_called()

    @patch("storybuilder.downloader.cli._download_stories")
    @patch("storybuilder.downloader.cli._scrape_subcategories")
    @patch("storybuilder.downloader.cli.load_cache")
    @patch("storybuilder.downloader.cli.save_cache")
    @patch("storybuilder.downloader.cli.get_subcategories")
    @patch("storybuilder.downloader.cli._print_config")
    @patch("storybuilder.downloader.cli._parse_dates")
    @patch("storybuilder.downloader.cli._setup_network")
    def test_main_early_return_on_invalid_dates(self, mock_net, mock_dates, mock_print, mock_subs, mock_save, mock_load, mock_scrape, mock_dl) -> None:
        """main() returns early when _parse_dates returns None."""
        from storybuilder.downloader.cli import main
        import argparse

        mock_dates.return_value = (None, None)  # Invalid dates

        with patch("storybuilder.downloader.cli._parse_args") as pa:
            pa.return_value = argparse.Namespace(
                category="gay", start_date="bad", end_date=None,
                output_dir="out", delay=0, force=False, socks5_proxy=None,
                rotate_on_refusal=False, max_workers=1, max_scraping=1,
                db="", gcs_bucket="", gcs_prefix="", s3_bucket="", s3_prefix=""
            )
            with patch("storybuilder.downloader.cli._setup_network", return_value=True):
                main()

        # Should not load cache or scrape
        mock_load.assert_not_called()
        mock_scrape.assert_not_called()

    @patch("storybuilder.downloader.cli._download_stories")
    @patch("storybuilder.downloader.cli._scrape_subcategories")
    @patch("storybuilder.downloader.cli.load_cache")
    @patch("storybuilder.downloader.cli.save_cache")
    @patch("storybuilder.downloader.cli.get_subcategories")
    @patch("storybuilder.downloader.cli._print_config")
    @patch("storybuilder.downloader.cli._parse_dates")
    @patch("storybuilder.downloader.cli._setup_network")
    def test_main_early_return_on_no_subcategories(self, mock_net, mock_dates, mock_print, mock_subs, mock_save, mock_load, mock_scrape, mock_dl) -> None:
        """main() returns early when get_subcategories returns empty."""
        from storybuilder.downloader.cli import main
        import argparse

        mock_subs.return_value = []  # No subcategories

        with patch("storybuilder.downloader.cli._parse_args") as pa:
            pa.return_value = argparse.Namespace(
                category="gay", start_date="2024-01-01", end_date=None,
                output_dir="out", delay=0, force=False, socks5_proxy=None,
                rotate_on_refusal=False, max_workers=1, max_scraping=1,
                db="", gcs_bucket="", gcs_prefix="", s3_bucket="", s3_prefix=""
            )
            with patch("storybuilder.downloader.cli._setup_network", return_value=True):
                with patch("storybuilder.downloader.cli._parse_dates", return_value=(__import__("datetime").date(2024,1,1), __import__("datetime").date(2024,12,31))):
                    main()

        # Should NOT load cache (early return happens before cache load)
        mock_load.assert_not_called()
        mock_scrape.assert_not_called()


class TestCLICloudPaths(unittest.TestCase):
    """Tests for GCS/S3/cloud upload paths."""

    @patch("storybuilder.downloader.cli._upload_to_cloud")
    @patch("storybuilder.downloader.db.optimize_fts")
    @patch("storybuilder.downloader.db.close_db")
    @patch("storybuilder.downloader.cli._download_stories")
    @patch("storybuilder.downloader.cli._scrape_subcategories")
    @patch("storybuilder.downloader.cli.load_cache")
    @patch("storybuilder.downloader.cli.save_cache")
    @patch("storybuilder.downloader.cli.get_subcategories")
    @patch("storybuilder.downloader.cli._print_config")
    @patch("storybuilder.downloader.cli._parse_dates")
    @patch("storybuilder.downloader.cli._setup_network")
    def test_main_uploads_to_gcs_when_gcs_bucket_set(self, mock_net, mock_dates, mock_print, mock_subs, mock_save, mock_load, mock_scrape, mock_dl, mock_close, mock_opt, mock_upload) -> None:
        """main() calls _upload_to_cloud when db and gcs_bucket are provided."""
        from storybuilder.downloader.cli import main
        import argparse

        mock_subs.return_value = [{"name": "s", "url": "u"}]
        mock_scrape.return_value = {}
        mock_upload.return_value = True

        with patch("storybuilder.downloader.cli._parse_args") as pa:
            pa.return_value = argparse.Namespace(
                category="gay", start_date="2024-01-01", end_date=None,
                output_dir="out", delay=0, force=False, socks5_proxy=None,
                rotate_on_refusal=False, max_workers=1, max_scraping=1,
                db="stories.db", gcs_bucket="my-bucket", gcs_prefix="prefix/", s3_bucket="", s3_prefix=""
            )
            with patch("storybuilder.downloader.cli._setup_network", return_value=True):
                with patch("storybuilder.downloader.cli._parse_dates", return_value=(__import__("datetime").date(2024,1,1), __import__("datetime").date(2024,12,31))):
                    main()

        mock_opt.assert_called_once()
        mock_close.assert_called_once()
        mock_upload.assert_called_once()

    @patch("storybuilder.downloader.cli._upload_to_cloud")
    @patch("storybuilder.downloader.db.optimize_fts")
    @patch("storybuilder.downloader.db.close_db")
    @patch("storybuilder.downloader.cli._download_stories")
    @patch("storybuilder.downloader.cli._scrape_subcategories")
    @patch("storybuilder.downloader.cli.load_cache")
    @patch("storybuilder.downloader.cli.save_cache")
    @patch("storybuilder.downloader.cli.get_subcategories")
    @patch("storybuilder.downloader.cli._print_config")
    @patch("storybuilder.downloader.cli._parse_dates")
    @patch("storybuilder.downloader.cli._setup_network")
    def test_main_uploads_to_s3_when_s3_bucket_set(self, mock_net, mock_dates, mock_print, mock_subs, mock_save, mock_load, mock_scrape, mock_dl, mock_close, mock_opt, mock_upload) -> None:
        """main() calls _upload_to_cloud when db and s3_bucket are provided."""
        from storybuilder.downloader.cli import main
        import argparse

        mock_subs.return_value = [{"name": "s", "url": "u"}]
        mock_scrape.return_value = {}
        mock_upload.return_value = True

        with patch("storybuilder.downloader.cli._parse_args") as pa:
            pa.return_value = argparse.Namespace(
                category="gay", start_date="2024-01-01", end_date=None,
                output_dir="out", delay=0, force=False, socks5_proxy=None,
                rotate_on_refusal=False, max_workers=1, max_scraping=1,
                db="stories.db", gcs_bucket="", gcs_prefix="", s3_bucket="s3-bucket", s3_prefix="prefix/"
            )
            with patch("storybuilder.downloader.cli._setup_network", return_value=True):
                with patch("storybuilder.downloader.cli._parse_dates", return_value=(__import__("datetime").date(2024,1,1), __import__("datetime").date(2024,12,31))):
                    main()

        mock_opt.assert_called_once()
        mock_close.assert_called_once()
        mock_upload.assert_called_once()


class TestCLIInternalFunctions(unittest.TestCase):
    """Tests for internal CLI functions: _print_config, download orchestration."""

    def test_print_config_basic(self) -> None:
        """Test _print_config prints expected config."""
        from storybuilder.downloader.cli import _print_config
        import io
        import sys
        from unittest.mock import patch

        args = argparse.Namespace(
            category="gay",
            output_dir="/tmp/out",
            delay=1.0,
            force=False,
            socks5_proxy=None,
            rotate_on_refusal=False,
            max_workers=4,
            max_scraping=2,
            db="",
            gcs_bucket="",
            gcs_prefix="",
            s3_bucket="",
            s3_prefix="",
        )
        start = __import__("datetime").date(2024, 1, 1)
        end = __import__("datetime").date(2024, 12, 31)

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            _print_config(args, start, end)
            output = mock_stdout.getvalue()

        self.assertIn("gay", output)
        self.assertIn("/tmp/out", output)
        self.assertIn("1.0", output)
        self.assertIn("4", output)  # max_workers

    def test_print_config_with_db(self) -> None:
        """Test _print_config includes database when set."""
        from storybuilder.downloader.cli import _print_config
        import io
        from unittest.mock import patch

        args = argparse.Namespace(
            category="gay",
            output_dir="/tmp/out",
            delay=0,
            force=False,
            socks5_proxy=None,
            rotate_on_refusal=False,
            max_workers=1,
            max_scraping=1,
            db="stories.db",
            gcs_bucket="",
            gcs_prefix="",
            s3_bucket="",
            s3_prefix="",
        )
        start = __import__("datetime").date(2024, 1, 1)
        end = __import__("datetime").date(2024, 12, 31)

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            with patch("storybuilder.downloader.cli.db.init_db"):
                _print_config(args, start, end)
                output = mock_stdout.getvalue()

        self.assertIn("Database:", output)
        self.assertIn("stories.db", output)

    def test_print_config_with_proxy_and_rotation(self) -> None:
        """Test _print_config shows proxy and rotation settings."""
        from storybuilder.downloader.cli import _print_config
        import io
        from unittest.mock import patch

        args = argparse.Namespace(
            category="gay",
            output_dir="/tmp/out",
            delay=2.0,
            force=True,
            socks5_proxy="socks5://localhost:1080",
            rotate_on_refusal=True,
            max_workers=8,
            max_scraping=4,
            db="",
            gcs_bucket="",
            gcs_prefix="",
            s3_bucket="",
            s3_prefix="",
        )
        start = __import__("datetime").date(2024, 1, 1)
        end = __import__("datetime").date(2024, 12, 31)

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            _print_config(args, start, end)
            output = mock_stdout.getvalue()

        self.assertIn("SOCKS5 proxy:", output)
        self.assertIn("rotation", output.lower())
        self.assertIn("DISABLED", output)  # force disables early-stop

    def test_merge_targets_dedup_keys(self) -> None:
        """Test _merge_targets combines output_paths for same key."""
        from storybuilder.downloader.cli import _merge_targets

        all_targets = {}
        sub_targets = [
            {"key": ("cat", "slug1"), "url": "u1", "output_path": "p1", "date": "d"},
            {"key": ("cat", "slug1"), "url": "u1", "output_path": "p2", "date": "d"},
            {"key": ("cat", "slug2"), "url": "u2", "output_path": "p3", "date": "d"},
        ]
        _merge_targets(all_targets, sub_targets)

        self.assertEqual(len(all_targets), 2)
        self.assertEqual(len(all_targets[("cat", "slug1")]["output_paths"]), 2)
        self.assertEqual(len(all_targets[("cat", "slug2")]["output_paths"]), 1)

    @patch("storybuilder.downloader.cli.process_subcategory")
    def test_scrape_subcategories_parallel(self, mock_process) -> None:
        """Test parallel scraping when max_scraping > 1."""
        from storybuilder.downloader.cli import _scrape_subcategories

        mock_process.return_value = [
            {"key": ("c", "s"), "url": "u", "output_path": "p", "date": "2024-06-01"}
        ]

        subcategories = [{"name": "sub1", "url": "http://ex/1"}, {"name": "sub2", "url": "http://ex/2"}]
        args = argparse.Namespace(
            max_scraping=2, delay=0, force=False, output_dir="/tmp", category="gay"
        )
        start = __import__("datetime").date(2024, 1, 1)
        end = __import__("datetime").date(2024, 12, 31)

        result = _scrape_subcategories(subcategories, start, end, args)

        self.assertTrue(len(result) > 0)
        self.assertEqual(mock_process.call_count, 2)

    @patch("storybuilder.downloader.cli.process_subcategory")
    def test_scrape_subcategories_sequential(self, mock_process) -> None:
        """Test sequential scraping when max_scraping == 1."""
        from storybuilder.downloader.cli import _scrape_subcategories

        mock_process.return_value = [
            {"key": ("c", "s"), "url": "u", "output_path": "p", "date": "2024-06-01"}
        ]

        subcategories = [{"name": "sub1", "url": "http://ex/1"}]
        args = argparse.Namespace(
            max_scraping=1, delay=0, force=False, output_dir="/tmp", category="gay"
        )
        start = __import__("datetime").date(2024, 1, 1)
        end = __import__("datetime").date(2024, 12, 31)

        result = _scrape_subcategories(subcategories, start, end, args)

        self.assertTrue(len(result) > 0)
        mock_process.assert_called_once()

    @patch("storybuilder.downloader.cli.download_single_target")
    def test_download_stories_parallel(self, mock_download) -> None:
        """Test parallel download orchestration."""
        from storybuilder.downloader.cli import _download_stories_parallel

        mock_download.return_value = True

        targets = {
            ("c", "s1"): {"url": "u1", "output_paths": ["p1"], "date": "2024-06-01"},
            ("c", "s2"): {"url": "u2", "output_paths": ["p2"], "date": "2024-06-01"},
        }
        result = _download_stories_parallel(targets, max_workers=2, delay=0, force=False)

        self.assertEqual(result, 2)
        self.assertEqual(mock_download.call_count, 2)

    @patch("storybuilder.downloader.cli.download_single_target")
    def test_download_stories_sequential(self, mock_download) -> None:
        """Test sequential download orchestration."""
        from storybuilder.downloader.cli import _download_stories_sequential

        mock_download.return_value = True

        targets = {
            ("c", "s1"): {"url": "u1", "output_paths": ["p1"], "date": "2024-06-01"},
            ("c", "s2"): {"url": "u2", "output_paths": ["p2"], "date": "2024-06-01"},
        }
        result = _download_stories_sequential(targets, delay=0, force=False)

        self.assertEqual(result, 2)
        self.assertEqual(mock_download.call_count, 2)

    @patch("storybuilder.downloader.cli._download_stories_parallel")
    @patch("storybuilder.downloader.cli._download_stories_sequential")
    def test_download_stories_chooses_parallel(self, mock_seq, mock_par) -> None:
        """Test _download_stories chooses parallel when max_workers > 1."""
        from storybuilder.downloader.cli import _download_stories

        mock_par.return_value = 5
        mock_seq.return_value = 5

        targets = {("c", "s"): {"url": "u", "output_paths": ["p"], "date": "d"}}
        args = argparse.Namespace(max_workers=4, delay=0, force=False)

        result = _download_stories(targets, args)

        mock_par.assert_called_once()
        mock_seq.assert_not_called()

    @patch("storybuilder.downloader.cli._download_stories_parallel")
    @patch("storybuilder.downloader.cli._download_stories_sequential")
    def test_download_stories_chooses_sequential(self, mock_seq, mock_par) -> None:
        """Test _download_stories chooses sequential when max_workers == 1."""
        from storybuilder.downloader.cli import _download_stories

        mock_par.return_value = 5
        mock_seq.return_value = 5

        targets = {("c", "s"): {"url": "u", "output_paths": ["p"], "date": "d"}}
        args = argparse.Namespace(max_workers=1, delay=0, force=False)

        result = _download_stories(targets, args)

        mock_seq.assert_called_once()
        mock_par.assert_not_called()


class TestUploadToCloud(unittest.TestCase):
    """Tests for _upload_to_cloud function."""

    @patch("storybuilder.downloader.cli.upload_many_s3")
    @patch("storybuilder.downloader.cli.upload_many_gcs")
    def test_upload_to_cloud_s3_only(self, mock_gcs, mock_s3) -> None:
        """Test upload to S3 only when s3_bucket is set."""
        from storybuilder.downloader.cli import _upload_to_cloud
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create output file
            out_dir = os.path.join(tmpdir, "out")
            os.makedirs(out_dir)
            with open(os.path.join(out_dir, "story.txt"), "w") as f:
                f.write("test")

            args = argparse.Namespace(
                db="",
                output_dir=out_dir,
                s3_bucket="my-bucket",
                s3_prefix="prefix/",
                gcs_bucket="",
                gcs_prefix="",
            )
            _upload_to_cloud(args)

            mock_s3.assert_called_once()
            mock_gcs.assert_not_called()

    @patch("storybuilder.downloader.cli.upload_many_s3")
    @patch("storybuilder.downloader.cli.upload_many_gcs")
    def test_upload_to_cloud_gcs_only(self, mock_gcs, mock_s3) -> None:
        """Test upload to GCS only when gcs_bucket is set."""
        from storybuilder.downloader.cli import _upload_to_cloud
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, "out")
            os.makedirs(out_dir)
            with open(os.path.join(out_dir, "story.txt"), "w") as f:
                f.write("test")

            args = argparse.Namespace(
                db="",
                output_dir=out_dir,
                s3_bucket="",
                s3_prefix="",
                gcs_bucket="my-gcs-bucket",
                gcs_prefix="gcs-prefix/",
            )
            _upload_to_cloud(args)

            mock_gcs.assert_called_once()
            mock_s3.assert_not_called()

    @patch("storybuilder.downloader.cli.upload_many_s3")
    @patch("storybuilder.downloader.cli.upload_many_gcs")
    def test_upload_to_cloud_fallback_to_nifty_index(self, mock_gcs, mock_s3) -> None:
        """Test fallback to nifty-index when no cloud buckets set but db exists."""
        from storybuilder.downloader.cli import _upload_to_cloud
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, "out")
            os.makedirs(out_dir)
            db_path = os.path.join(tmpdir, "stories.db")
            with open(db_path, "w") as f:
                f.write("fake db")

            args = argparse.Namespace(
                db=db_path,
                output_dir=out_dir,
                s3_bucket="",
                s3_prefix="",
                gcs_bucket="",
                gcs_prefix="",
            )
            _upload_to_cloud(args)

            # Should fallback to nifty-index
            mock_gcs.assert_called_with("nifty-index", [db_path], source_directory=tmpdir)

    @patch("storybuilder.downloader.cli.upload_many_s3")
    @patch("storybuilder.downloader.cli.upload_many_gcs")
    def test_upload_to_cloud_handles_empty_output(self, mock_gcs, mock_s3) -> None:
        """Test upload handles non-existent output directory."""
        from storybuilder.downloader.cli import _upload_to_cloud
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, "nonexistent")

            args = argparse.Namespace(
                db="",
                output_dir=out_dir,
                s3_bucket="my-bucket",
                s3_prefix="prefix/",
                gcs_bucket="",
                gcs_prefix="",
            )
            _upload_to_cloud(args)

            # Should still try to upload (empty file list is OK)
            mock_s3.assert_called_once()


class TestStorageFunctions(unittest.TestCase):
    """Tests for storage.py helper functions."""

    def test_s3_object_key_with_prefix(self) -> None:
        """Test _s3_object_key generates correct key with prefix."""
        from storybuilder.downloader.storage import _s3_object_key

        key = _s3_object_key("prefix", "path/to/file.txt")
        self.assertEqual(key, "prefix/path/to/file.txt")

    def test_s3_object_key_without_prefix(self) -> None:
        """Test _s3_object_key generates correct key without prefix."""
        from storybuilder.downloader.storage import _s3_object_key

        key = _s3_object_key("", "path/to/file.txt")
        self.assertEqual(key, "path/to/file.txt")

    def test_upload_many_gcs_empty_returns_early(self) -> None:
        """upload_many_gcs returns immediately when filenames is empty."""
        from storybuilder.downloader.storage import upload_many_gcs

        # Should return without error
        result = upload_many_gcs("bucket", "prefix", [])
        self.assertIsNone(result)

    def test_upload_many_s3_empty_returns_early(self) -> None:
        """upload_many_s3 returns immediately when filenames is empty."""
        from storybuilder.downloader.storage import upload_many_s3

        result = upload_many_s3("bucket", "prefix", [])
        self.assertIsNone(result)

    def test_upload_many_uses_gcs(self) -> None:
        """upload_many delegates to upload_many_gcs."""
        from storybuilder.downloader.storage import upload_many
        from unittest.mock import patch

        with patch("storybuilder.downloader.storage.upload_many_gcs") as mock_gcs:
            upload_many("bucket", ["file.txt"], source_directory="src")
            mock_gcs.assert_called_once()

if __name__ == "__main__":
    unittest.main()
