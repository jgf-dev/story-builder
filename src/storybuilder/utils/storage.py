import logging
import os
from pathlib import Path

from huggingface_hub import BucketInfo
from huggingface_hub import HfApi
from huggingface_hub import bucket_info
from huggingface_hub.errors import BucketNotFoundError

from storybuilder.utils.env import load_env
from storybuilder.utils.logging_config import configure_logging
from storybuilder.utils.logging_config import get_logger


configure_logging(level=logging.INFO, format_string="%(message)s")

REPO_ID = "jeremygf/stories"
logger = get_logger(__name__)

configure_logging()


def get_hf_client(token: str = "HF_TOKEN") -> HfApi:  # noqa
	"""
	Get a Hugging Face Hub client.

	Returns:
	    A Hugging Face Hub client.
	"""
	load_env()

	token_value = os.getenv(token)
	if not token_value:
		message = f"Hugging Face token environment variable '{token}' is not set or is empty."
		raise ValueError(message)

	return HfApi(token=token_value)


def upload_file_to_hf(
	hf: HfApi,
	file_path: Path,
	repo_id: str = REPO_ID,
	path_in_repo: str | None = None,
) -> None:
	"""
	Upload a file to Hugging Face Hub.

	Args:
	    hf (HfApi): The Hugging Face Hub client.
	    file_path (Path): The path to the file to upload.
	    repo_id (str): The repository or bucket ID on Hugging Face Hub.
	    path_in_repo (str | None): The path where the file should be saved in the repository or bucket.
	        If None, defaults to `file_path.name`.
	"""
	if path_in_repo is None:
		path_in_repo = file_path.name

	if is_hf_bucket(repo_id):
		hf.batch_bucket_files(
			repo_id,
			add=[(file_path, path_in_repo)],
		)
		return

	hf.upload_file(
		path_or_fileobj=file_path,
		path_in_repo=path_in_repo,
		repo_id=repo_id,
	)


def upload_directory_to_hf(
	hf: HfApi,
	directory_path: Path,
	repo_id: str = REPO_ID,
	path_in_repo: str | None = None,
) -> None:
	"""
	Upload a directory to Hugging Face Hub.

	Args:
	    hf (HfApi): The Hugging Face Hub client.
	    directory_path (Path): The path to the directory to upload.
	    repo_id (str): The repository or bucket ID on Hugging Face Hub.
	    path_in_repo (str | None): The destination path prefix in the repository or bucket.
	        If None, defaults to `directory_path.name`. If an empty string, files will be uploaded
	        to the root of the repository/bucket.
	"""
	if not directory_path.is_dir():
		message = f"Directory not found: {directory_path}"
		raise FileNotFoundError(message)

	if path_in_repo is None:
		path_in_repo = directory_path.name

	if is_hf_bucket(repo_id):
		additions = []
		for path in sorted(directory_path.rglob("*.db")):
			if path.is_file():
				rel_path = path.relative_to(directory_path)
				target_path = f"{path_in_repo}/{rel_path}" if path_in_repo else str(rel_path)

				additions.append((path, target_path))

		if len(additions) == 0:
			message = f"No .db files found in {directory_path}"
			raise ValueError(message)

		logger.info("Uploading %s .db files to bucket %s...", len(additions), repo_id)

		hf.batch_bucket_files(
			repo_id,
			add=additions,  # type: ignore
		)
		return

	hf.upload_folder(
		repo_id=repo_id,
		folder_path=directory_path,
		path_in_repo=path_in_repo or None,
		allow_patterns=["*.db"],  # Include all sqlite files
	)


def is_hf_bucket(repo_id: str) -> bool:
	"""Return True if the provided repo_id identifies a Hugging Face bucket."""
	try:
		bucket_info(repo_id)
	except BucketNotFoundError:
		return False
	else:
		return True


def upload_story_db(hf: HfApi, repo_id: str = REPO_ID, path_in_repo: str | None = None) -> None:
	"""
	Upload the story database to Hugging Face Hub.

	Args:
	    hf (HfApi): The Hugging Face Hub client.
	    repo_id (str): The repository ID on Hugging Face Hub.
	    path_in_repo (str | None): The destination path prefix in the repository or bucket.
	"""
	try:
		bucket_info_result: BucketInfo = bucket_info(repo_id)
		logger.info("Bucket info for %s: %s", repo_id, bucket_info_result)
		upload_directory_to_hf(hf, Path.cwd() / "stories" / "db", repo_id, path_in_repo=path_in_repo)
	except BucketNotFoundError as err:
		logger.exception("Error occurred while checking bucket info for %s", repo_id)
		message = f"Bucket '{repo_id}' not found. Please create the bucket first."
		raise BucketNotFoundError(message, response=err.response) from err


if __name__ == "__main__":
	hf_client = get_hf_client()
	upload_story_db(hf_client)
