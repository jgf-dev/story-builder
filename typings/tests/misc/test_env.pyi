from _typeshed import Incomplete

import os
import unittest
from pathlib import Path
from unittest.mock import patch


class TestEnvModule(unittest.TestCase):
    def setUp(self) -> None: ...

    def tearDown(self) -> None: ...

    @patch("storybuilder.utils.env.load_dotenv")
    def test_load_env_single_call(self, mock_load_dotenv: Incomplete) -> None: ...

    @patch("storybuilder.utils.env.load_dotenv")
    def test_load_env_with_custom_path(self, mock_load_dotenv: Incomplete) -> None: ...

    @patch("storybuilder.utils.env.load_dotenv")
    def test_get_api_key_required_success(self, mock_load_dotenv: Incomplete) -> None: ...

    @patch("storybuilder.utils.env.load_dotenv")
    def test_get_api_key_required_missing(self, mock_load_dotenv: Incomplete) -> None: ...

    @patch("storybuilder.utils.env.load_dotenv")
    def test_get_api_key_optional_missing(self, mock_load_dotenv: Incomplete) -> None: ...

    @patch("storybuilder.utils.env.load_dotenv")
    def test_get_stable_api_key_single_key(self, mock_load_dotenv: Incomplete) -> None: ...

    @patch("storybuilder.utils.env.load_dotenv")
    def test_get_stable_api_key_returns_only_primary(self, mock_load_dotenv: Incomplete) -> None: ...

    @patch("storybuilder.utils.env.load_dotenv")
    def test_get_api_keys_with_rotation_all(self, mock_load_dotenv: Incomplete) -> None: ...

    @patch("storybuilder.utils.env.load_dotenv")
    def test_get_api_keys_with_rotation_primary_only(self, mock_load_dotenv: Incomplete) -> None: ...

    @patch("storybuilder.utils.env.load_dotenv")
    def test_get_api_keys_with_rotation_none(self, mock_load_dotenv: Incomplete) -> None: ...


class TestLoggingConfig(unittest.TestCase):
    def setUp(self) -> None: ...

    @patch("storybuilder.utils.logging_config.logging.basicConfig")
    def test_configure_logging_single_call(self, mock_basicConfig: Incomplete) -> None: ...

    @patch("storybuilder.utils.logging_config.logging.basicConfig")
    def test_configure_logging_with_force(self, mock_basicConfig: Incomplete) -> None: ...
