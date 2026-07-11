import glob
import os
from pathlib import Path
from typing import Any

from google.cloud.storage import Client
from google.cloud.storage import transfer_manager


def _normalize_filenames(filenames: list[str], source_directory: str) -> list[str]:
    """Normalize filenames for uploads.

    If source_directory is provided, absolute paths under it are converted to
    relative paths. Absolute paths outside it fall back to basename.
    """
    if not source_directory:
        return filenames

    base_dir = Path(source_directory).resolve()
    normalized: list[str] = []
    for filename in filenames:
        path = Path(filename)
        # First, interpret the filename as it was provided (often rooted at cwd).
        try:
            normalized.append(str(path.resolve().relative_to(base_dir)))
            continue
        except ValueError as exc:
            # Expected when the resolved path is not under source_directory.
            _ = exc

        # Next, interpret the filename as already relative to source_directory.
        if not path.is_absolute():
            try:
                normalized.append(str((base_dir / path).resolve().relative_to(base_dir)))
                continue
            except ValueError as exc:
                # Expected when the combined path is still outside source_directory.
                _ = exc

        # Outside source_directory; fall back to basename.
        normalized.append(path.name)
    return normalized


def _upload_many_gcs_legacy(
    bucket_name: str,
    prefix: str,
    filenames: list[str],
    source_directory: str = "",
    workers: int = 8,
) -> None:
    """Upload files to GCS using transfer_manager with an optional object prefix.

    Returns immediately when filenames is empty.
    """
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


def _upload_many_s3_legacy(
    bucket_name: str,
    prefix: str,
    filenames: list[str],
    source_directory: str = "",
) -> None:
    """Upload files to S3 with keys rooted at the optional prefix.
    Returns immediately when filenames is empty. Requires boto3 at runtime.
    """
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
        path = Path(filename)

        if base_dir:
            # Prefer the path as provided (often already rooted at cwd).
            try:
                source_path = path.resolve()
                source_path.relative_to(base_dir)
            except ValueError:
                # Otherwise, interpret it as relative to source_directory.
                source_path = (base_dir / path).resolve() if not path.is_absolute() else path.resolve()

            try:
                relative_name = str(source_path.relative_to(base_dir))
            except ValueError:
                relative_name = source_path.name
        else:
            source_path = path
            relative_name = path.name

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


def upload_many_gcs(
    bucket_name: str,
    prefix: str,
    filenames: list[str],
    source_directory: str = "",
    workers: int = 8,
) -> None:
    """Upload files to GCS using transfer_manager with an optional object prefix.

    Returns immediately when filenames is empty.
    """
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
    extra_args = {}
    expected_owner = os.getenv("AWS_EXPECTED_BUCKET_OWNER")
    if expected_owner:
        extra_args["ExpectedBucketOwner"] = expected_owner

    s3_client.upload_file(
        str(source_path),
        bucket_name,
        s3_key,
        ExtraArgs=extra_args or None,
    )
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
