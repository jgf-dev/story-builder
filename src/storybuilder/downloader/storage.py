import glob
import os
from pathlib import Path

<<<<<<< HEAD
from google.cloud.storage import Client
from google.cloud.storage import transfer_manager


def upload_many(
    bucket_name: str, filenames: list[str], source_directory: str = "", workers: int = 8,

):
    """Upload every file in a list to a bucket, concurrently in a process pool.
=======
import concurrent.futures
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from google.cloud.storage import Client, transfer_manager


def upload_many_gcs(
    bucket_name: str,
    prefix: str,
    filenames: list[str],
    source_directory: str = "",
    workers: int = 8,
):
    """Upload every file in a list to a bucket, concurrently in a process pool."""
    try:
        storage_client = Client()
        bucket = storage_client.bucket(bucket_name)
>>>>>>> origin/implement-cloud-output-adapters-6981127355945556911

        results = transfer_manager.upload_many_from_filenames(
            bucket,
            filenames,
            source_directory=source_directory,
            blob_name_prefix=prefix + "/"
            if prefix and not prefix.endswith("/")
            else prefix,
            max_workers=workers,
        )

        for name, result in zip(filenames, results):
            if isinstance(result, Exception):
                print(f"Failed to upload {name} to GCS due to exception: {result}")
            else:
                pass  # print(f"Uploaded {name} to GCS.")
    except Exception as e:
        print(f"Failed to initialize GCS upload: {e}")

<<<<<<< HEAD
    results = transfer_manager.upload_many_from_filenames(
        bucket,
        filenames,
        source_directory=source_directory,
        max_workers=workers,

    )
=======
>>>>>>> origin/implement-cloud-output-adapters-6981127355945556911

def _upload_single_s3(s3_client, bucket_name, object_name, file_path):
    try:
        s3_client.upload_file(file_path, bucket_name, object_name)
        return None
    except (BotoCoreError, ClientError) as e:
        return e
    except Exception as e:
        return e

<<<<<<< HEAD
        if isinstance(result, Exception):
            print(f"Failed to upload {name} due to exception: {result}")
        else:
            print(f"Uploaded {name} to {bucket.name}.")
=======

def upload_many_s3(
    bucket_name: str,
    prefix: str,
    filenames: list[str],
    source_directory: str = "",
    workers: int = 8,
):
    """Upload every file in a list to an S3 bucket, concurrently using a thread pool."""
    try:
        s3_client = boto3.client("s3")

        # Ensure prefix ends with a slash if it's not empty
        if prefix and not prefix.endswith("/"):
            prefix += "/"

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_file = {}
            for filename in filenames:
                # Calculate object name
                rel_path = (
                    os.path.relpath(filename, source_directory)
                    if source_directory
                    else os.path.basename(filename)
                )

                # Replace Windows path separators if needed
                rel_path = rel_path.replace(os.sep, "/")

                object_name = f"{prefix}{rel_path}"
                future = executor.submit(
                    _upload_single_s3, s3_client, bucket_name, object_name, filename
                )
                future_to_file[future] = filename

            for future in concurrent.futures.as_completed(future_to_file):
                filename = future_to_file[future]
                try:
                    result = future.result()
                    if isinstance(result, Exception):
                        print(
                            f"Failed to upload {filename} to S3 due to exception: {result}"
                        )
                    else:
                        pass  # print(f"Uploaded {filename} to S3.")
                except Exception as exc:
                    print(
                        f"Failed to upload {filename} to S3 due to unhandled exception: {exc}"
                    )
    except Exception as e:
        print(f"Failed to initialize S3 upload: {e}")
>>>>>>> origin/implement-cloud-output-adapters-6981127355945556911


if __name__ == "__main__":
    directory = Path(os.getenv("STORIES_DB")).resolve()
    print(directory)

    files_to_upload = glob.glob(str(directory / "*.db"))

    print(f"Found {len(files_to_upload)} files to upload.")
    print(files_to_upload)

    upload_many_gcs("nifty-index", "", files_to_upload, source_directory=str(directory))
