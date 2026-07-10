import glob
import os
from pathlib import Path

from google.cloud.storage import Client
from google.cloud.storage import transfer_manager


def upload_many(
    bucket_name: str, filenames: list[str], source_directory: str = "", workers: int = 8
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
        bucket, filenames, source_directory=source_directory, max_workers=workers
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
