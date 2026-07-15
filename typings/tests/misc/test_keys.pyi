import os
import unittest
from pathlib import Path
from unittest.mock import patch
from storybuilder.utils.env import load_env
from tests.helpers_external_fakes import live_api_enabled
from tests.helpers_external_fakes import make_fake_genai_client


class TestKeys(unittest.TestCase):
    def test_vertex_ai_client(self) -> None: ...
