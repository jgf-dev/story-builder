from _typeshed import Incomplete

import unittest
from unittest.mock import MagicMock
from unittest.mock import patch
from storybuilder.downloader.network import rotate_windscribe_ip


class TestRotateWindscribeIp(unittest.TestCase):
    @patch("storybuilder.downloader.network.safe_print")
    @patch("storybuilder.downloader.network.time.sleep")
    @patch("subprocess.run")
    def test_rotate_windscribe_ip_success(self, mock_run: Incomplete, mock_sleep: Incomplete, mock_safe_print: Incomplete) -> None: ...

    @patch("storybuilder.downloader.network.safe_print")
    @patch("subprocess.run")
    def test_rotate_windscribe_ip_failure(self, mock_run: Incomplete, mock_safe_print: Incomplete) -> None: ...

    @patch("storybuilder.downloader.network.safe_print")
    @patch("subprocess.run")
    def test_rotate_windscribe_ip_exception(self, mock_run: Incomplete, mock_safe_print: Incomplete) -> None: ...
