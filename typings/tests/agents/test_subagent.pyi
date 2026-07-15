from google.genai.types import SafetySetting
import os
import unittest
from pathlib import Path
from unittest.mock import patch
from dotenv import load_dotenv
from google.genai import types
from tests.helpers_external_fakes import (
    live_api_enabled,
    make_fake_genai_client,
)


class TestSubagent(unittest.TestCase):
    def test_analyzer_direct(self) -> None: ...
