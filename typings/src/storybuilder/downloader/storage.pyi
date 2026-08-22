import glob
import os
from pathlib import Path
from typing import Any
from google.cloud.storage import Client, transfer_manager


def upload_many(bucket_name: str, filenames: list[str], source_directory: str = "", workers: int = 8) -> None: ...


def upload_many_gcs(bucket_name: str, prefix: str, filenames: list[str], source_directory: str = "", workers: int = 8) -> None: ...


def upload_many_s3(bucket_name: str, prefix: str, filenames: list[str], source_directory: str = "", workers: int = 8) -> None: ...
