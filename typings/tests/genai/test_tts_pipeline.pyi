import glob
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from storybuilder.utils.env import load_env
from tests.helpers_external_fakes import fake_process_file_factory
from tests.helpers_external_fakes import live_api_enabled

MAX_API_CALLS: Literal[3] = 3


class TestTTSPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None: ...

    def test_sequential_tts_generation_with_voice_continuity(self) -> None: ...


class TestProcessFileIdWarning(unittest.TestCase):
    def test_missing_interaction_id_logs_warning(self) -> None: ...
