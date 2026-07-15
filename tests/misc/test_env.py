import os
import unittest
from pathlib import Path
from unittest.mock import patch


class TestEnvModule(unittest.TestCase):
    def setUp(self) -> None:
        self.env_backup = os.environ.copy()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.env_backup)
        import storybuilder.utils.env as env_module
        env_module._env_loaded = False

    @patch("storybuilder.utils.env.load_dotenv")
    def test_load_env_single_call(self, mock_load_dotenv) -> None:
        import storybuilder.utils.env as env_module
        env_module._env_loaded = False
        env_module.load_env()
        env_module.load_env()
        mock_load_dotenv.assert_called_once()

    @patch("storybuilder.utils.env.load_dotenv")
    def test_load_env_with_custom_path(self, mock_load_dotenv) -> None:
        import storybuilder.utils.env as env_module
        env_module._env_loaded = False
        custom_path = Path("/custom/.env")
        env_module.load_env(dotenv_path=custom_path)
        mock_load_dotenv.assert_called_once_with(dotenv_path=custom_path)

    @patch("storybuilder.utils.env.load_dotenv")
    def test_get_api_key_required_success(self, mock_load_dotenv) -> None:
        import storybuilder.utils.env as env_module
        env_module._env_loaded = False
        os.environ["TEST_API_KEY"] = "test-value"
        result = env_module.get_api_key("TEST_API_KEY", required=True)
        self.assertEqual(result, "test-value")

    @patch("storybuilder.utils.env.load_dotenv")
    def test_get_api_key_required_missing(self, mock_load_dotenv) -> None:
        import storybuilder.utils.env as env_module
        env_module._env_loaded = False
        with self.assertRaises(ValueError) as ctx:
            env_module.get_api_key("MISSING_KEY", required=True)
        self.assertIn("MISSING_KEY", str(ctx.exception))

    @patch("storybuilder.utils.env.load_dotenv")
    def test_get_api_key_optional_missing(self, mock_load_dotenv) -> None:
        import storybuilder.utils.env as env_module
        env_module._env_loaded = False
        result = env_module.get_optional_api_key("MISSING_KEY")
        self.assertIsNone(result)

    @patch("storybuilder.utils.env.load_dotenv")
    def test_get_stable_api_key_single_key(self, mock_load_dotenv) -> None:
        import storybuilder.utils.env as env_module
        env_module._env_loaded = False
        os.environ["GEMINI_API_KEY"] = "primary-key"
        result = env_module.get_stable_api_key("GEMINI_API_KEY")
        self.assertEqual(result, "primary-key")

    @patch("storybuilder.utils.env.load_dotenv")
    def test_get_stable_api_key_returns_only_primary(self, mock_load_dotenv) -> None:
        import storybuilder.utils.env as env_module
        env_module._env_loaded = False
        os.environ["GEMINI_API_KEY"] = "primary-key"
        os.environ["GEMINI_API_KEY_1"] = "rotated-key-1"
        os.environ["GEMINI_API_KEY_2"] = "rotated-key-2"
        result = env_module.get_stable_api_key("GEMINI_API_KEY")
        self.assertEqual(result, "primary-key")

    @patch("storybuilder.utils.env.load_dotenv")
    def test_get_api_keys_with_rotation_all(self, mock_load_dotenv) -> None:
        import storybuilder.utils.env as env_module
        env_module._env_loaded = False
        os.environ["GEMINI_API_KEY"] = "primary-key"
        os.environ["GEMINI_API_KEY_1"] = "rotated-key-1"
        os.environ["GEMINI_API_KEY_2"] = "rotated-key-2"
        result = env_module.get_api_keys_with_rotation("GEMINI_API_KEY")
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], ("GEMINI_API_KEY", "primary-key"))
        self.assertEqual(result[1], ("GEMINI_API_KEY_1", "rotated-key-1"))
        self.assertEqual(result[2], ("GEMINI_API_KEY_2", "rotated-key-2"))

    @patch("storybuilder.utils.env.load_dotenv")
    def test_get_api_keys_with_rotation_primary_only(self, mock_load_dotenv) -> None:
        import storybuilder.utils.env as env_module
        env_module._env_loaded = False
        os.environ["GEMINI_API_KEY"] = "primary-key"
        result = env_module.get_api_keys_with_rotation("GEMINI_API_KEY")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], ("GEMINI_API_KEY", "primary-key"))

    @patch("storybuilder.utils.env.load_dotenv")
    def test_get_api_keys_with_rotation_none(self, mock_load_dotenv) -> None:
        import storybuilder.utils.env as env_module
        env_module._env_loaded = False
        result = env_module.get_api_keys_with_rotation("GEMINI_API_KEY")
        self.assertEqual(result, [])


class TestLoggingConfig(unittest.TestCase):
    def setUp(self) -> None:
        import storybuilder.utils.logging_config as lc
        lc._configured = False

    @patch("storybuilder.utils.logging_config.logging.basicConfig")
    def test_configure_logging_single_call(self, mock_basicConfig) -> None:
        import storybuilder.utils.logging_config as lc
        lc._configured = False
        lc.configure_logging()
        lc.configure_logging()
        mock_basicConfig.assert_called_once()

    @patch("storybuilder.utils.logging_config.logging.basicConfig")
    def test_configure_logging_with_force(self, mock_basicConfig) -> None:
        import storybuilder.utils.logging_config as lc
        lc._configured = False
        lc.configure_logging()
        lc.configure_logging(force=True)
        self.assertEqual(mock_basicConfig.call_count, 2)


if __name__ == "__main__":
    unittest.main()