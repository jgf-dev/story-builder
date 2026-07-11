import glob
import os
from pathlib import Path

from google.cloud.storage import Client
from google.cloud.storage import transfer_manager


import boto3

def upload_many_s3(
    bucket_name: str,
    prefix: str,
    filenames: list[str],
    source_directory: str = "",
    workers: int = 8,
):
    """Upload every file in a list to an S3 bucket.

    Each object key is derived from the filename, excluding the
    `source_directory` parameter, and prefixed with `prefix`.
    """
    import concurrent.futures
    import traceback

    s3_client = boto3.client("s3")

    def upload_file(filename):
        try:
            rel_path = os.path.relpath(filename, source_directory)
            object_name = f"{prefix}/{rel_path}".replace("//", "/")
            s3_client.upload_file(filename, bucket_name, object_name)
            return filename, None
        except Exception as e:
            return filename, e

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(upload_file, fn): fn for fn in filenames}
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            try:
                filename, result = future.result()
                if result is not None:
                    print(f"Failed to upload {filename} to S3 due to exception: {result}")
                else:
                    print(f"Uploaded {filename} to s3://{bucket_name}/{prefix}")
            except Exception as e:
                print(f"Failed to upload {name} to S3 due to exception: {e}")


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


if __name__ == "__main__":
    directory = Path(os.getenv("STORIES_DB")).resolve()
    print(directory)

    files_to_upload = glob.glob(str(directory / "*.db"))

    print(f"Found {len(files_to_upload)} files to upload.")
    print(files_to_upload)

    upload_many("nifty-index", files_to_upload, source_directory=str(directory))
