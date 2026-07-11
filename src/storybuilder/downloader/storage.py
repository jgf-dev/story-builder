import glob
import os
from pathlib import Path
from typing import Any

from google.cloud.storage import Client
from google.cloud.storage import transfer_manager


def upload_many(
    bucket_name: str, filenames: list[str], source_directory: str = "", workers: int = 8,
):
    """Upload every file in a list to a bucket, concurrently in a process pool.

    Each blob name is derived from the filename, not including the
    `source_directory` parameter. For complete control of the blob name for each
    file (and other aspects of individual blob metadata), use
    transfer_manager.upload_many() instead.
    """

    storage_client = Client()
    bucket = storage_client.bucket(bucket_name)

    results = transfer_manager.upload_many_from_filenames(
        bucket,
        filenames,
        source_directory=source_directory,
        max_workers=workers,
    )

    for name, result in zip(filenames, results):
        # The results list is either `None` or an exception for each filename in
        # the input list, in order.

        if isinstance(result, Exception):
            print(f"Failed to upload {name} due to exception: {result}")
        else:
            print(f"Uploaded {name} to {bucket.name}.")


def upload_many_gcs(
    bucket_name: str,
    prefix: str,
    filenames: list[str],
    source_directory: str = "",
    workers: int = 8,
) -> None:
    """CLI-compatible GCS upload (prefix reserved; blob names from filenames)."""
    del prefix  # blob key prefixing not yet applied by transfer_manager helper
    upload_many(
        bucket_name,
        filenames,
        source_directory=source_directory,
        workers=workers,
    )


def _resolve_s3_source(filename: str, base_dir: Path | None) -> tuple[Path, str]:
    """Return (source_path, relative_name) for building an S3 object key."""
    path = Path(filename)
    if base_dir is None:
        return path, path.name

    try:
        source_path = path.resolve()
        source_path.relative_to(base_dir)
    except ValueError:
        source_path = path.resolve() if path.is_absolute() else (base_dir / path).resolve()

    try:
        relative_name = str(source_path.relative_to(base_dir))
    except ValueError:
        relative_name = source_path.name

    return source_path, relative_name.replace(os.sep, "/")


def _s3_object_key(key_prefix: str, relative_name: str) -> str:
    if not key_prefix:
        return relative_name
    return f"{key_prefix}/{relative_name}"


def _upload_single_s3(
    s3_client: Any,
    bucket_name: str,
    key_prefix: str,
    filename: str,
    base_dir: Path | None,
) -> None:
    source_path, relative_name = _resolve_s3_source(filename, base_dir)
    s3_key = _s3_object_key(key_prefix, relative_name)
    s3_client.upload_file(str(source_path), bucket_name, s3_key)
    print(f"Uploaded {source_path} to s3://{bucket_name}/{s3_key}")


def upload_many_s3(
    bucket_name: str,
    prefix: str,
    filenames: list[str],
    source_directory: str = "",
    workers: int = 8,
) -> None:
    """Upload files to S3 with keys rooted at the optional prefix.

    Returns immediately when filenames is empty. Requires boto3 at runtime.
    """
    del workers  # sequential uploads; reserved for future parallelism
    if not filenames:
        return

    try:
        import boto3
    except ImportError as exc:
        raise ImportError(
            "S3 uploads require the 'boto3' package. Install it with `pip install boto3`.",
        ) from exc

    s3_client = boto3.client("s3")
    base_dir = Path(source_directory).resolve() if source_directory else None
    key_prefix = prefix.strip("/")

    for filename in filenames:
        _upload_single_s3(s3_client, bucket_name, key_prefix, filename, base_dir)


if __name__ == "__main__":
    directory = Path(os.getenv("STORIES_DB")).resolve()
    print(directory)

    files_to_upload = glob.glob(str(directory / "*.db"))

    print(f"Found {len(files_to_upload)} files to upload.")
    print(files_to_upload)

    upload_many("nifty-index", files_to_upload, source_directory=str(directory))
