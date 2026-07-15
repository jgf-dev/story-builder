import os
import unittest
from pathlib import Path
from unittest.mock import patch
from dotenv import load_dotenv
from tests.helpers_external_fakes import (
    live_api_enabled,
    make_fake_genai_client,
)


class TestKeys(unittest.TestCase):
    def test_vertex_ai_client(self) -> None: ...
