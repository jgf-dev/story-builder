import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import BucketInfo
from huggingface_hub import HfApi
from huggingface_hub import bucket_info
from huggingface_hub.errors import BucketNotFoundError
from storybuilder.utils.logging_config import configure_logging, get_logger

REPO_ID: Literal['jeremygf/stories'] = "jeremygf/stories"
logger: Logger


def get_hf_client(token: str = "HF_TOKEN") -> HfApi: ...


def upload_file_to_hf(hf: HfApi, file_path: Path, repo_id: str = ..., path_in_repo: str | None = None) -> None: ...


def upload_directory_to_hf(hf: HfApi, directory_path: Path, repo_id: str = ..., path_in_repo: str | None = None) -> None: ...


def is_hf_bucket(repo_id: str) -> bool: ...


def upload_story_db(hf: HfApi, repo_id: str = ..., path_in_repo: str | None = None) -> None: ...
