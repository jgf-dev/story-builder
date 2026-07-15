import io
import unittest
from contextlib import redirect_stderr
from importlib.metadata import PackageNotFoundError
from importlib.metadata import distribution
from unittest.mock import patch
from storybuilder.genai import client
from storybuilder.genai import tts


class TestTtsEntrypoint(unittest.TestCase):
    def test_tts_module_reexports_client_main(self) -> None: ...

    def test_console_script_entry_point_declared(self) -> None: ...

    def test_main_exits_nonzero_for_missing_dir(self) -> None: ...
