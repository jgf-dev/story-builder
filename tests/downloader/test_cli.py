import unittest
from unittest.mock import patch, MagicMock
import argparse
import sys

from storybuilder.downloader.cli import _setup_network
from storybuilder.downloader import network

class TestCLI(unittest.TestCase):
    def setUp(self):
        # Reset network state before each test
        self.original_proxies = network.PROXIES
        self.original_rotation = network.ENABLE_ROTATION
        network.PROXIES = None
        network.ENABLE_ROTATION = False

    def tearDown(self):
        # Restore network state after each test
        network.PROXIES = self.original_proxies
        network.ENABLE_ROTATION = self.original_rotation

    def test_setup_network_no_options(self):
        args = argparse.Namespace(socks5_proxy=None, rotate_on_refusal=False)
        result = _setup_network(args)

        self.assertTrue(result)
        self.assertIsNone(network.PROXIES)
        self.assertFalse(network.ENABLE_ROTATION)

    @patch('builtins.print')
    def test_setup_network_proxy_no_socks_module(self, mock_print):
        args = argparse.Namespace(socks5_proxy="192.168.1.1:1080", rotate_on_refusal=False)

        # We need to simulate ImportError when importing 'socks'
        with patch.dict('sys.modules', {'socks': None}):
            result = _setup_network(args)

        self.assertFalse(result)
        self.assertIsNone(network.PROXIES)
        mock_print.assert_any_call("Error: SOCKS proxy support requires the 'pysocks' package.")

    def test_setup_network_proxy_without_prefix(self):
        args = argparse.Namespace(socks5_proxy="192.168.1.1:1080", rotate_on_refusal=False)

        # Make sure 'socks' module is available
        mock_socks = MagicMock()
        with patch.dict('sys.modules', {'socks': mock_socks}):
            result = _setup_network(args)

        self.assertTrue(result)
        expected_url = "socks5h://192.168.1.1:1080"
        self.assertEqual(network.PROXIES, {"http": expected_url, "https": expected_url})
        self.assertFalse(network.ENABLE_ROTATION)

    def test_setup_network_proxy_with_prefix(self):
        args = argparse.Namespace(socks5_proxy="socks5://192.168.1.1:1080", rotate_on_refusal=False)

        mock_socks = MagicMock()
        with patch.dict('sys.modules', {'socks': mock_socks}):
            result = _setup_network(args)

        self.assertTrue(result)
        expected_url = "socks5://192.168.1.1:1080"
        self.assertEqual(network.PROXIES, {"http": expected_url, "https": expected_url})

    def test_setup_network_rotation_enabled(self):
        args = argparse.Namespace(socks5_proxy=None, rotate_on_refusal=True)

        result = _setup_network(args)

        self.assertTrue(result)
        self.assertIsNone(network.PROXIES)
        self.assertTrue(network.ENABLE_ROTATION)

if __name__ == '__main__':
    unittest.main()