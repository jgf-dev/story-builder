import glob
import os
from pathlib import Path

import boto3
from google.cloud.storage import Client
from google.cloud.storage import transfer_manager


def _normalize_filenames(filenames: list[str], source_directory: str) -> list[str]:
    if not source_directory:
        return filenames

    base_dir = Path(source_directory).resolve()
    normalized: list[str] = []
    for filename in filenames:
        path = Path(filename)
        if path.is_absolute():
            try:
                normalized.append(str(path.resolve().relative_to(base_dir)))
            except ValueError:
                normalized.append(path.name)
        else:
            normalized.append(filename)
    return normalized


def upload_many_gcs(
    bucket_name: str,
    prefix: str,
    filenames: list[str],
    source_directory: str = "",
    workers: int = 8,
) -> None:
    if not filenames:
        return

    normalized_filenames = _normalize_filenames(filenames, source_directory)
    blob_name_prefix = f"{prefix.strip('/')}/" if prefix else ""

    storage_client = Client()
    bucket = storage_client.bucket(bucket_name)
    results = transfer_manager.upload_many_from_filenames(
        bucket,
        normalized_filenames,
        source_directory=source_directory,
        blob_name_prefix=blob_name_prefix,
        max_workers=workers,
    )

    for name, result in zip(normalized_filenames, results):
        if isinstance(result, Exception):
            print(f"Failed to upload {name} due to exception: {result}")
        else:
            print(f"Uploaded {name} to gs://{bucket.name}/{blob_name_prefix}{name}")


def upload_many_s3(
    bucket_name: str,
    prefix: str,
    filenames: list[str],
    source_directory: str = "",
) -> None:
    if not filenames:
        return

    s3_client = boto3.client("s3")
    base_dir = Path(source_directory).resolve() if source_directory else None
    key_prefix = prefix.strip("/")

    for filename in filenames:
        source_path = Path(filename)
        if base_dir:
            try:
                relative_name = str(source_path.resolve().relative_to(base_dir))
            except ValueError:
                relative_name = source_path.name
        else:
            relative_name = source_path.name

        relative_name = relative_name.replace(os.sep, "/")
        s3_key = f"{key_prefix}/{relative_name}" if key_prefix else relative_name
        s3_client.upload_file(str(source_path), bucket_name, s3_key)
        print(f"Uploaded {source_path} to s3://{bucket_name}/{s3_key}")


def upload_many(
    bucket_name: str,
    filenames: list[str],
    source_directory: str = "",
    workers: int = 8,
) -> None:
    upload_many_gcs(
        bucket_name,
        "",
        filenames,
        source_directory=source_directory,
        workers=workers,
    )


if __name__ == "__main__":
    directory = Path(os.getenv("STORIES_DB")).resolve()
    print(directory)

    files_to_upload = glob.glob(str(directory / "*.db"))

    print(f"Found {len(files_to_upload)} files to upload.")
    print(files_to_upload)

    upload_many("nifty-index", files_to_upload, source_directory=str(directory))
