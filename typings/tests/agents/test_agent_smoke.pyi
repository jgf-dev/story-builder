from _typeshed import Incomplete

import asyncio
import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from dotenv import load_dotenv
from google.genai import types
from tests.helpers_external_fakes import fake_run_async, live_api_enabled


class TestAgentSmoke(unittest.IsolatedAsyncioTestCase):
    async def test_agent_smoke(self) -> Incomplete: ...
