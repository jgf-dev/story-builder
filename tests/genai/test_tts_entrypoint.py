"""Regression tests for the genai-tts console entrypoint."""

import unittest
from importlib.metadata import entry_points

from storybuilder.genai import client
from storybuilder.genai import tts


class TestTtsEntrypoint(unittest.TestCase):
    def test_tts_module_reexports_client_main(self) -> None:
        self.assertIs(tts.main, client.main)
        self.assertIs(tts.process_directory, client.process_directory)
        self.assertTrue(callable(tts.main))

    def test_console_script_entry_point_declared(self) -> None:
        eps = entry_points()
        scripts = (
            eps.select(group="console_scripts")
            if hasattr(eps, "select")
            else eps.get("console_scripts", [])
        )
        genai_tts = next((ep for ep in scripts if ep.name == "genai-tts"), None)
        self.assertIsNotNone(genai_tts, "genai-tts console script missing from package metadata")
        self.assertEqual(genai_tts.value, "storybuilder.genai.tts:main")
        self.assertIs(genai_tts.load(), client.main)


if __name__ == "__main__":
    unittest.main()
