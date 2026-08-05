import unittest
from unittest.mock import patch, MagicMock

from storybuilder.downloader.network import rotate_windscribe_ip


class TestRotateWindscribeIp(unittest.TestCase):
    @patch("storybuilder.downloader.network.safe_print")
    @patch("storybuilder.downloader.network.time.sleep")
    @patch("subprocess.run")
    def test_rotate_windscribe_ip_success(self, mock_run, mock_sleep, mock_safe_print) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = rotate_windscribe_ip()

        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["windscribe-cli", "ip", "rotate"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        mock_sleep.assert_called_once_with(10)

    @patch("storybuilder.downloader.network.safe_print")
    @patch("subprocess.run")
    def test_rotate_windscribe_ip_failure(self, mock_run, mock_safe_print) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "Command failed"
        mock_run.return_value = mock_result

        result = rotate_windscribe_ip()

        self.assertFalse(result)
        mock_safe_print.assert_any_call("Failed to rotate IP: Command failed")

    @patch("storybuilder.downloader.network.safe_print")
    @patch("subprocess.run")
    def test_rotate_windscribe_ip_exception(self, mock_run, mock_safe_print) -> None:
        mock_run.side_effect = Exception("File not found")

        result = rotate_windscribe_ip()

        self.assertFalse(result)
        mock_safe_print.assert_any_call(
            "Error running windscribe-cli ip rotate: File not found"
        )
