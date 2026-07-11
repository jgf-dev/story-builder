"""Regression tests for the genai-tts console entrypoint."""

import io
import unittest
from contextlib import redirect_stderr
from importlib.metadata import PackageNotFoundError
from importlib.metadata import distribution
from unittest.mock import patch

from storybuilder.genai import client
from storybuilder.genai import tts


class TestTtsEntrypoint(unittest.TestCase):
    def test_tts_module_reexports_client_main(self) -> None:
        self.assertIs(tts.main, client.main)
        self.assertIs(tts.process_directory, client.process_directory)
        self.assertTrue(callable(tts.main))

    def test_console_script_entry_point_declared(self) -> None:
        try:
            dist = distribution("storybuilder")
        except PackageNotFoundError:
            self.skipTest(
                "storybuilder distribution metadata unavailable "
                "(e.g. PYTHONPATH=src without install)",
            )

        scripts = [ep for ep in dist.entry_points if ep.group == "console_scripts"]
        genai_tts = next((ep for ep in scripts if ep.name == "genai-tts"), None)
        self.assertIsNotNone(genai_tts, "genai-tts console script missing from package metadata")
        self.assertEqual(genai_tts.value, "storybuilder.genai.tts:main")
        self.assertIs(genai_tts.load(), client.main)

    def test_main_exits_nonzero_for_missing_dir(self) -> None:
        stderr = io.StringIO()
        with (
            patch("sys.argv", ["genai-tts", "--dir", "/nonexistent/path/for/tts"]),
            redirect_stderr(stderr),
            self.assertRaises(SystemExit) as raised,
        ):
            client.main()
        self.assertNotEqual(raised.exception.code, 0)
        self.assertIn("does not exist", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
