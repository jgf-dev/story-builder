# ruff: noqa
import os
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

from huggingface_hub import HfApi

from storybuilder.utils.storage import (
    get_hf_client,
    upload_file_to_hf,
    upload_directory_to_hf,
    upload_story_db,
)


class TestStorage(unittest.TestCase):
    def test_get_hf_client_success(self) -> None:
        # Test that it successfully gets the client when the env var is set
        with (
            patch("storybuilder.utils.env.load_env"),
            patch.dict(os.environ, {"HF_TOKEN": "my-secret-val"}),
        ):
            client = get_hf_client("HF_TOKEN")
            self.assertIsInstance(client, HfApi)
            self.assertEqual(client.token, "my-secret-val")

    def test_get_hf_client_missing_raises_value_error(self) -> None:
        # Test that it raises ValueError when the env var is missing
        with (
            patch("storybuilder.utils.env.load_env"),
            patch.dict(os.environ, {}, clear=True),
        ):
            with self.assertRaises(ValueError) as context:
                get_hf_client("HF_TOKEN")
            self.assertIn(
                "Hugging Face token environment variable 'HF_TOKEN' is not set",
                str(context.exception),
            )

    def test_get_hf_client_empty_raises_value_error(self) -> None:
        # Test that it raises ValueError when the env var is empty
        with (
            patch("storybuilder.utils.env.load_env"),
            patch.dict(os.environ, {"HF_TOKEN": ""}),
        ):
            with self.assertRaises(ValueError) as context:
                get_hf_client("HF_TOKEN")
            self.assertIn(
                "Hugging Face token environment variable 'HF_TOKEN' is not set or is empty",
                str(context.exception),
            )

    def test_get_hf_client_custom_env_var(self) -> None:
        # Test that it works with a custom environment variable name
        with (
            patch("storybuilder.utils.env.load_env"),
            patch.dict(os.environ, {"CUSTOM_TOKEN_VAR": "custom-val"}),
        ):
            client = get_hf_client("CUSTOM_TOKEN_VAR")
            self.assertIsInstance(client, HfApi)
            self.assertEqual(client.token, "custom-val")

    def test_upload_file_to_hf_non_bucket_default(self) -> None:
        mock_hf = MagicMock(spec=HfApi)
        with patch("storybuilder.utils.storage.is_hf_bucket", return_value=False):
            upload_file_to_hf(mock_hf, Path("dir/subdir/file.db"), repo_id="my-repo")
            mock_hf.upload_file.assert_called_once_with(
                path_or_fileobj=Path("dir/subdir/file.db"),
                path_in_repo="file.db",
                repo_id="my-repo",
            )

    def test_upload_file_to_hf_non_bucket_custom_path(self) -> None:
        mock_hf = MagicMock(spec=HfApi)
        with patch("storybuilder.utils.storage.is_hf_bucket", return_value=False):
            upload_file_to_hf(
                mock_hf,
                Path("dir/subdir/file.db"),
                repo_id="my-repo",
                path_in_repo="custom/file.db",
            )
            mock_hf.upload_file.assert_called_once_with(
                path_or_fileobj=Path("dir/subdir/file.db"),
                path_in_repo="custom/file.db",
                repo_id="my-repo",
            )

    def test_upload_file_to_hf_bucket_default(self) -> None:
        mock_hf = MagicMock(spec=HfApi)
        with patch("storybuilder.utils.storage.is_hf_bucket", return_value=True):
            upload_file_to_hf(mock_hf, Path("dir/subdir/file.db"), repo_id="my-bucket")
            mock_hf.batch_bucket_files.assert_called_once_with(
                "my-bucket",
                add=[(Path("dir/subdir/file.db"), "file.db")],
            )

    def test_upload_file_to_hf_bucket_custom_path(self) -> None:
        mock_hf = MagicMock(spec=HfApi)
        with patch("storybuilder.utils.storage.is_hf_bucket", return_value=True):
            upload_file_to_hf(
                mock_hf,
                Path("dir/subdir/file.db"),
                repo_id="my-bucket",
                path_in_repo="custom/file.db",
            )
            mock_hf.batch_bucket_files.assert_called_once_with(
                "my-bucket",
                add=[(Path("dir/subdir/file.db"), "custom/file.db")],
            )

    def test_upload_directory_to_hf_non_bucket(self) -> None:
        mock_hf = MagicMock(spec=HfApi)
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir_path = Path(tmpdir)
            db_file = temp_dir_path / "foo.db"
            db_file.touch()

            with patch("storybuilder.utils.storage.is_hf_bucket", return_value=False):
                upload_directory_to_hf(mock_hf, temp_dir_path, repo_id="my-repo")
                mock_hf.upload_folder.assert_called_once_with(
                    repo_id="my-repo",
                    folder_path=temp_dir_path,
                    path_in_repo=temp_dir_path.name,
                    allow_patterns=["*.db"],
                )

    def test_upload_directory_to_hf_bucket_default(self) -> None:
        mock_hf = MagicMock(spec=HfApi)
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir_path = Path(tmpdir)
            db_file = temp_dir_path / "foo.db"
            db_file.touch()

            with (
                patch("storybuilder.utils.storage.is_hf_bucket", return_value=True),
                self.assertLogs("storybuilder.utils.storage", level="INFO") as log_capture,
            ):
                upload_directory_to_hf(mock_hf, temp_dir_path, repo_id="my-bucket")
                expected_dest = f"{temp_dir_path.name}/foo.db"
                mock_hf.batch_bucket_files.assert_called_once_with(
                    "my-bucket",
                    add=[(db_file, expected_dest)],
                )
                self.assertTrue(
                    any(
                        "Uploading 1 .db files to bucket my-bucket" in log
                        for log in log_capture.output
                    )
                )

    def test_upload_directory_to_hf_bucket_custom_path(self) -> None:
        mock_hf = MagicMock(spec=HfApi)
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir_path = Path(tmpdir)
            db_file = temp_dir_path / "foo.db"
            db_file.touch()

            with patch("storybuilder.utils.storage.is_hf_bucket", return_value=True):
                upload_directory_to_hf(
                    mock_hf, temp_dir_path, repo_id="my-bucket", path_in_repo=""
                )
                mock_hf.batch_bucket_files.assert_called_once_with(
                    "my-bucket",
                    add=[(db_file, "foo.db")],
                )

    def test_upload_story_db_success(self) -> None:
        mock_hf = MagicMock(spec=HfApi)
        with (
            patch("storybuilder.utils.storage.bucket_info") as mock_bucket_info,
            patch("storybuilder.utils.storage.upload_directory_to_hf") as mock_upload_dir,
            self.assertLogs("storybuilder.utils.storage", level="INFO") as log_capture,
        ):
            mock_bucket_info.return_value = "some-bucket-info"
            upload_story_db(mock_hf, repo_id="my-repo", path_in_repo="my-custom-prefix")

            mock_bucket_info.assert_called_once_with("my-repo")
            mock_upload_dir.assert_called_once_with(
                mock_hf,
                Path.cwd() / "stories" / "db",
                "my-repo",
                path_in_repo="my-custom-prefix",
            )
            self.assertTrue(
                any(
                    "Bucket info for my-repo: some-bucket-info" in log
                    for log in log_capture.output
                )
            )

    def test_upload_story_db_not_found(self) -> None:
        mock_hf = MagicMock(spec=HfApi)
        from huggingface_hub.errors import BucketNotFoundError

        mock_response = MagicMock()
        with (
            patch(
                "storybuilder.utils.storage.bucket_info",
                side_effect=BucketNotFoundError("Not Found", response=mock_response),
            ),
            self.assertLogs("storybuilder.utils.storage", level="ERROR") as log_capture,
        ):
            with self.assertRaises(BucketNotFoundError):
                upload_story_db(mock_hf, repo_id="missing-repo")
            self.assertTrue(
                any(
                    "Error occurred while checking bucket info for missing-repo" in log
                    for log in log_capture.output
                )
            )


if __name__ == "__main__":
    unittest.main()
