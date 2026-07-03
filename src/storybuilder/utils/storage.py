import os
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import BucketInfo
from huggingface_hub import HfApi
from huggingface_hub import bucket_info
from huggingface_hub.errors import BucketNotFoundError


load_dotenv()  # Load environment variables from .env file

REPO_ID = "jeremygf/stories"
HF_TOKEN = os.getenv("HF_TOKEN")

hf = HfApi(token=HF_TOKEN)


def upload_file_to_hf(file_path: Path, repo_id: str = REPO_ID) -> None:
    """
    Upload a file to Hugging Face Hub.

    Args:
        file_path (Path): The path to the file to upload.
        repo_id (str): The repository or bucket ID on Hugging Face Hub.
    """
    if is_hf_bucket(repo_id):
        hf.batch_bucket_files(
            repo_id,
            add=[(file_path, file_path.name)],
            token=HF_TOKEN,
        )
        return

    hf.upload_file(
        path_or_fileobj=file_path,
        path_in_repo=file_path.name,
        repo_id=repo_id,
        token=HF_TOKEN,
    )


def upload_directory_to_hf(directory_path: Path, repo_id: str = REPO_ID) -> None:
    """
    Upload a directory to Hugging Face Hub.

    Args:
        directory_path (Path): The path to the directory to upload.
        repo_id (str): The repository or bucket ID on Hugging Face Hub.
    """
    if not directory_path.is_dir():
        message = f"Directory not found: {directory_path}"
        raise FileNotFoundError(message)

    if is_hf_bucket(repo_id):
        db_files = [
            path
            for path in sorted(directory_path.rglob("*.db"))
            if path.is_file()
        ]
        if not db_files:
            message = f"No .db files found in {directory_path}"
            raise ValueError(message)

        additions = [
            (path, str(path.relative_to(directory_path)))
            for path in db_files
        ]
        if additions is not None:
            print(f"Uploading {len(additions)} .db files to bucket {repo_id}...")
            hf.batch_bucket_files(
                repo_id,
                add=additions,  # type: ignore
                token=HF_TOKEN,
            )
        return

    hf.upload_folder(
        repo_id=repo_id,
        folder_path=directory_path,
        path_in_repo=directory_path.name,
        token=HF_TOKEN,
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


def get_bucket_info(repo_id: str = REPO_ID) -> BucketInfo:
    """
    Get information about a bucket on Hugging Face Hub.

    Returns:
        Information about the bucket.
    """
    return bucket_info(repo_id)


def upload_story_db(repo_id: str = REPO_ID) -> None:
    """
    Upload the story database to Hugging Face Hub.

    Args:
        repo_id (str): The repository ID on Hugging Face Hub.
    """
    try:
        bucket_info_result = get_bucket_info(repo_id)
        print(f"Bucket info for {repo_id}: {bucket_info_result}")
        upload_directory_to_hf(Path.cwd() / "stories" / "db", repo_id)
    except BucketNotFoundError as e:
        print(f"Error occurred while checking bucket info for {repo_id}: {e}")


if __name__ == "__main__":
    upload_story_db()
