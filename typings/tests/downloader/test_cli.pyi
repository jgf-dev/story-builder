from _typeshed import Incomplete

import argparse
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch
from storybuilder.downloader import network
from storybuilder.downloader.cli import _setup_network


class TestCLI(unittest.TestCase):
    original_proxies: dict[str, str] | None
    original_rotation: bool

    def setUp(self) -> None: ...

    def tearDown(self) -> None: ...

    def test_setup_network_no_options(self) -> None: ...

    @patch("builtins.print")
    def test_setup_network_proxy_no_socks_module(self, mock_print: Incomplete) -> None: ...

    def test_setup_network_proxy_without_prefix(self) -> None: ...

    def test_setup_network_proxy_with_prefix(self) -> None: ...

    def test_setup_network_rotation_enabled(self) -> None: ...


class TestCLIArgsAndDates(unittest.TestCase):
    def test_parse_args_required_category(self) -> None: ...

    def test_parse_dates_valid(self) -> None: ...

    def test_parse_dates_invalid_start(self) -> None: ...

    def test_parse_dates_no_end_uses_today(self) -> None: ...

    def test_merge_targets_dedups(self) -> None: ...


class TestCLICacheIntegration(unittest.TestCase):
    @patch("storybuilder.downloader.cli.load_cache")
    @patch("storybuilder.downloader.cli.save_cache")
    @patch("storybuilder.downloader.cli.get_subcategories")
    @patch("storybuilder.downloader.cli._scrape_subcategories")
    @patch("storybuilder.downloader.cli._upload_to_cloud")
    @patch("storybuilder.downloader.cli._download_stories")
    def test_main_loads_and_saves_cache(self, mock_download: Incomplete, mock_upload: Incomplete, mock_scrape: Incomplete, mock_get_subs: Incomplete, mock_save: Incomplete, mock_load: Incomplete) -> None: ...


class TestCLIEarlyReturns(unittest.TestCase):
    @patch("storybuilder.downloader.cli._download_stories")
    @patch("storybuilder.downloader.cli._scrape_subcategories")
    @patch("storybuilder.downloader.cli.load_cache")
    @patch("storybuilder.downloader.cli.save_cache")
    @patch("storybuilder.downloader.cli.get_subcategories")
    @patch("storybuilder.downloader.cli._print_config")
    @patch("storybuilder.downloader.cli._parse_dates")
    @patch("storybuilder.downloader.cli._setup_network")
    def test_main_early_return_on_network_failure(self, mock_net: Incomplete, mock_dates: Incomplete, mock_print: Incomplete, mock_subs: Incomplete, mock_save: Incomplete, mock_load: Incomplete, mock_scrape: Incomplete, mock_dl: Incomplete) -> None: ...

    @patch("storybuilder.downloader.cli._download_stories")
    @patch("storybuilder.downloader.cli._scrape_subcategories")
    @patch("storybuilder.downloader.cli.load_cache")
    @patch("storybuilder.downloader.cli.save_cache")
    @patch("storybuilder.downloader.cli.get_subcategories")
    @patch("storybuilder.downloader.cli._print_config")
    @patch("storybuilder.downloader.cli._parse_dates")
    @patch("storybuilder.downloader.cli._setup_network")
    def test_main_early_return_on_invalid_dates(self, mock_net: Incomplete, mock_dates: Incomplete, mock_print: Incomplete, mock_subs: Incomplete, mock_save: Incomplete, mock_load: Incomplete, mock_scrape: Incomplete, mock_dl: Incomplete) -> None: ...

    @patch("storybuilder.downloader.cli._download_stories")
    @patch("storybuilder.downloader.cli._scrape_subcategories")
    @patch("storybuilder.downloader.cli.load_cache")
    @patch("storybuilder.downloader.cli.save_cache")
    @patch("storybuilder.downloader.cli.get_subcategories")
    @patch("storybuilder.downloader.cli._print_config")
    @patch("storybuilder.downloader.cli._parse_dates")
    @patch("storybuilder.downloader.cli._setup_network")
    def test_main_early_return_on_no_subcategories(self, mock_net: Incomplete, mock_dates: Incomplete, mock_print: Incomplete, mock_subs: Incomplete, mock_save: Incomplete, mock_load: Incomplete, mock_scrape: Incomplete, mock_dl: Incomplete) -> None: ...


class TestCLICloudPaths(unittest.TestCase):
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
    def test_main_uploads_to_gcs_when_gcs_bucket_set(self, mock_net: Incomplete, mock_dates: Incomplete, mock_print: Incomplete, mock_subs: Incomplete, mock_save: Incomplete, mock_load: Incomplete, mock_scrape: Incomplete, mock_dl: Incomplete, mock_close: Incomplete, mock_opt: Incomplete, mock_upload: Incomplete) -> None: ...

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
    def test_main_uploads_to_s3_when_s3_bucket_set(self, mock_net: Incomplete, mock_dates: Incomplete, mock_print: Incomplete, mock_subs: Incomplete, mock_save: Incomplete, mock_load: Incomplete, mock_scrape: Incomplete, mock_dl: Incomplete, mock_close: Incomplete, mock_opt: Incomplete, mock_upload: Incomplete) -> None: ...


class TestCLIInternalFunctions(unittest.TestCase):
    def test_print_config_basic(self) -> None: ...

    def test_print_config_with_db(self) -> None: ...

    def test_print_config_with_proxy_and_rotation(self) -> None: ...

    def test_merge_targets_dedup_keys(self) -> None: ...

    @patch("storybuilder.downloader.cli.process_subcategory")
    def test_scrape_subcategories_parallel(self, mock_process: Incomplete) -> None: ...

    @patch("storybuilder.downloader.cli.process_subcategory")
    def test_scrape_subcategories_sequential(self, mock_process: Incomplete) -> None: ...

    @patch("storybuilder.downloader.cli.download_single_target")
    def test_download_stories_parallel(self, mock_download: Incomplete) -> None: ...

    @patch("storybuilder.downloader.cli.download_single_target")
    def test_download_stories_sequential(self, mock_download: Incomplete) -> None: ...

    @patch("storybuilder.downloader.cli._download_stories_parallel")
    @patch("storybuilder.downloader.cli._download_stories_sequential")
    def test_download_stories_chooses_parallel(self, mock_seq: Incomplete, mock_par: Incomplete) -> None: ...

    @patch("storybuilder.downloader.cli._download_stories_parallel")
    @patch("storybuilder.downloader.cli._download_stories_sequential")
    def test_download_stories_chooses_sequential(self, mock_seq: Incomplete, mock_par: Incomplete) -> None: ...


class TestUploadToCloud(unittest.TestCase):
    @patch("storybuilder.downloader.cli.upload_many_s3")
    @patch("storybuilder.downloader.cli.upload_many_gcs")
    def test_upload_to_cloud_s3_only(self, mock_gcs: Incomplete, mock_s3: Incomplete) -> None: ...

    @patch("storybuilder.downloader.cli.upload_many_s3")
    @patch("storybuilder.downloader.cli.upload_many_gcs")
    def test_upload_to_cloud_gcs_only(self, mock_gcs: Incomplete, mock_s3: Incomplete) -> None: ...

    @patch("storybuilder.downloader.cli.upload_many_s3")
    @patch("storybuilder.downloader.cli.upload_many_gcs")
    def test_upload_to_cloud_fallback_to_nifty_index(self, mock_gcs: Incomplete, mock_s3: Incomplete) -> None: ...

    @patch("storybuilder.downloader.cli.upload_many_s3")
    @patch("storybuilder.downloader.cli.upload_many_gcs")
    def test_upload_to_cloud_handles_empty_output(self, mock_gcs: Incomplete, mock_s3: Incomplete) -> None: ...


class TestStorageFunctions(unittest.TestCase):
    def test_s3_object_key_with_prefix(self) -> None: ...

    def test_s3_object_key_without_prefix(self) -> None: ...

    def test_upload_many_gcs_empty_returns_early(self) -> None: ...

    def test_upload_many_s3_empty_returns_early(self) -> None: ...

    def test_upload_many_uses_gcs(self) -> None: ...
