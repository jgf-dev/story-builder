from _typeshed import Incomplete

import asyncio
import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from google.genai import types
from storybuilder.utils.env import load_env
from tests.helpers_external_fakes import fake_run_async
from tests.helpers_external_fakes import live_api_enabled


class TestAgentSmoke(unittest.IsolatedAsyncioTestCase):
    async def test_agent_smoke(self) -> Incomplete: ...
