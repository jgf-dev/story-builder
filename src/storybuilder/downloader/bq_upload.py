#!/usr/bin/env python3
"""Upload SQLite database tables (e.g. stories/db/stories.db) to Google BigQuery datasets.

Supports batched chunk uploads (via NDJSON file loads or GCS staging), automatic schema
mapping, dry-run mode, and progress tracking.

Usage:
    python -m storybuilder.downloader.bq_upload --dataset my_dataset [--db stories/db/stories.db] [--table stories]
    storybuilder-bq --dataset my_dataset --gcs-bucket my_bucket --dry-run
"""

import argparse
import json
import logging
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Generator

logger = logging.getLogger(__name__)

# Default batch size for NDJSON chunks to prevent memory overload
DEFAULT_BATCH_SIZE = 5000


def get_sqlite_schema(conn: sqlite3.Connection, table_name: str) -> list[dict[str, Any]]:
    """Inspect SQLite table and return list of column info dicts.

    Each dict has keys: name, type, notnull, dflt_value, pk.
    """
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    rows = cursor.fetchall()
    if not rows:
        raise ValueError(f"Table '{table_name}' does not exist or has no columns in SQLite DB.")

    columns = []
    for row in rows:
        columns.append({
            "cid": row[0],
            "name": row[1],
            "type": row[2].upper() if row[2] else "TEXT",
            "notnull": bool(row[3]),
            "dflt_value": row[4],
            "pk": bool(row[5]),
        })
    return columns


def map_sqlite_to_bq_schema(columns: list[dict[str, Any]]) -> list[Any]:
    """Map SQLite column types to BigQuery SchemaFields.

    Requires google-cloud-bigquery.
    """
    try:
        from google.cloud import bigquery
    except ImportError as e:
        raise ImportError(
            "google-cloud-bigquery is required for BigQuery uploads. "
            "Install it via `pip install google-cloud-bigquery`."
        ) from e

    bq_schema = []
    for col in columns:
        col_type = col["type"]
        name = col["name"]
        mode = "NULLABLE"  # BigQuery standard default

        if "INT" in col_type:
            field_type = "INT64"
        elif "REAL" in col_type or "FLOAT" in col_type or "DOUBLE" in col_type:
            field_type = "FLOAT64"
        elif "BOOL" in col_type:
            field_type = "BOOL"
        elif "DATE" in col_type or "TIME" in col_type:
            field_type = "TIMESTAMP" if "TIME" in col_type or "DATETIME" in col_type else "STRING"
        else:
            field_type = "STRING"

        bq_schema.append(bigquery.SchemaField(name, field_type, mode=mode))
    return bq_schema


def fetch_sqlite_rows_in_batches(
    conn: sqlite3.Connection,
    table_name: str,
    columns: list[str],
    batch_size: int = DEFAULT_BATCH_SIZE,
    limit: int = 0,
    offset: int = 0,
) -> Generator[list[dict[str, Any]], None, None]:
    """Generator fetching rows from a SQLite table in batches as dictionaries."""
    cursor = conn.cursor()
    cols_sql = ", ".join(f'"{c}"' for c in columns)
    sql = f"SELECT {cols_sql} FROM {table_name}"
    if limit > 0:
        sql += f" LIMIT {limit}"
        if offset > 0:
            sql += f" OFFSET {offset}"
    elif offset > 0:
        sql += f" LIMIT -1 OFFSET {offset}"

    cursor.execute(sql)



    records_fetched = 0
    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break

        batch = [dict(zip(columns, row, strict=False)) for row in rows]
        records_fetched += len(batch)
        yield batch

        if limit > 0 and records_fetched >= limit:
            break


MAX_BQ_ROW_BYTES = 90_000_000  # ~90 MB limit per row to respect BigQuery 100MB row size limit


def sanitize_record_for_json(record: dict[str, Any], max_bytes: int = MAX_BQ_ROW_BYTES) -> dict[str, Any]:
    """Ensure dictionary values are JSON serializable for NDJSON export and stay under BigQuery row size limits."""
    sanitized: dict[str, Any] = {}
    for k, v in record.items():
        if v is None:
            sanitized[k] = None
        elif isinstance(v, (int, float, str, bool)):
            sanitized[k] = v
        elif isinstance(v, bytes):
            sanitized[k] = v.decode("utf-8", errors="replace")
        else:
            sanitized[k] = str(v)

    # Truncate content string if it exceeds BigQuery max row size limit (100 MB)
    content_str = sanitized.get("content")
    if isinstance(content_str, str) and len(content_str) > max_bytes:
        orig_len = len(content_str)
        logger.warning(
            "Truncating row content for record %s (original char count: %d) to fit BigQuery 100MB limit",
            record.get("id") or record.get("path"),
            orig_len,
        )
        sanitized["content"] = (
            content_str[:max_bytes]
            + f"\n[TRUNCATED: Exceeded BigQuery 100MB row size limit from original {orig_len:,} chars]"
        )

    return sanitized



def upload_sqlite_to_bigquery(
    db_path: str | Path,
    dataset_id: str,
    table_name: str = "stories",
    project_id: str | None = None,
    location: str = "US",
    batch_size: int = DEFAULT_BATCH_SIZE,
    gcs_bucket: str | None = None,
    gcs_prefix: str = "bq_stage",
    write_disposition: str = "WRITE_TRUNCATE",
    max_bad_records: int = 100,
    dry_run: bool = False,
    limit: int = 0,
    offset: int = 0,
) -> dict[str, Any]:


    """Upload a SQLite table to a BigQuery table in batches.

    Args:
        db_path: Path to the SQLite database file.
        dataset_id: BigQuery target dataset ID.
        table_name: SQLite table name & target BigQuery table name.
        project_id: GCP project ID. If None, resolves from environment/active config.
        location: BigQuery dataset location (default: 'US').
        batch_size: Number of records per upload batch.
        gcs_bucket: Optional GCS bucket name for staging NDJSON uploads.
        gcs_prefix: GCS object prefix when staging uploads.
        write_disposition: BigQuery WriteDisposition ('WRITE_TRUNCATE', 'WRITE_APPEND', 'WRITE_EMPTY').
        dry_run: If True, inspect schema and print execution plan without uploading data.
        limit: Max rows to upload (0 for all rows).

    Returns:
        Summary dict containing status, rows_uploaded, elapsed_seconds, and table_id.
    """
    try:
        from google.cloud import bigquery
    except ImportError as e:
        raise ImportError(
            "google-cloud-bigquery is required for BigQuery uploads. "
            "Install it via `pip install google-cloud-bigquery`."
        ) from e

    db_path = Path(db_path).resolve()
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite database file not found at: {db_path}")

    conn = sqlite3.connect(str(db_path))
    try:
        sqlite_cols = get_sqlite_schema(conn, table_name)
        col_names = [col["name"] for col in sqlite_cols]
        bq_schema = map_sqlite_to_bq_schema(sqlite_cols)

        count_cursor = conn.cursor()
        total_rows_query = f"SELECT COUNT(*) FROM {table_name}"
        if limit > 0:
            total_rows_query = f"SELECT MIN(({total_rows_query}), {limit})"
        total_rows = count_cursor.execute(total_rows_query).fetchone()[0]

        print(f"Database:        {db_path}")
        print(f"Table:           {table_name}")
        print(f"Total Rows:      {total_rows:,}")
        print(f"Batch Size:      {batch_size:,}")
        print(f"Target Dataset:  {dataset_id}")

        if dry_run:
            print("\n[DRY RUN] Schema Mapping:")
            for sf in bq_schema:
                print(f"  - {sf.name}: {sf.field_type} ({sf.mode})")
            print(f"[DRY RUN] Would process ~{(total_rows + batch_size - 1) // batch_size} batches.")
            return {
                "status": "dry_run",
                "rows_uploaded": 0,
                "total_rows": total_rows,
                "elapsed_seconds": 0.0,
                "table_id": f"{project_id or 'default'}.{dataset_id}.{table_name}",
            }

        client = bigquery.Client(project=project_id, location=location)

        # Ensure dataset exists
        dataset_ref = client.dataset(dataset_id)
        try:
            dataset = client.get_dataset(dataset_ref)
        except Exception:
            print(f"Creating BigQuery dataset '{client.project}.{dataset_id}' in {location}...")
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = location
            dataset = client.create_dataset(dataset, exists_ok=True)

        table_ref = dataset_ref.table(table_name)


        # Prepare GCS client if bucket provided
        gcs_storage_client = None
        if gcs_bucket:
            try:
                from google.cloud import storage
                gcs_storage_client = storage.Client(project=client.project)
            except ImportError as e:
                raise ImportError(
                    "google-cloud-storage is required when specifying --gcs-bucket. "
                    "Install it via `pip install google-cloud-storage`."
                ) from e

        start_time = time.time()
        rows_uploaded = 0
        batch_count = 0

        job_config = bigquery.LoadJobConfig(
            schema=bq_schema,
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            write_disposition=getattr(bigquery.WriteDisposition, write_disposition, bigquery.WriteDisposition.WRITE_TRUNCATE),
            ignore_unknown_values=True,
            max_bad_records=max_bad_records,
        )


        current_disposition = job_config.write_disposition

        with tempfile.TemporaryDirectory() as tmp_dir:
            for batch in fetch_sqlite_rows_in_batches(conn, table_name, col_names, batch_size=batch_size, limit=limit, offset=offset):
                batch_count += 1
                ndjson_path = Path(tmp_dir) / f"batch_{batch_count:05d}.jsonl"

                with open(ndjson_path, "w", encoding="utf-8") as f:
                    for record in batch:
                        sanitized = sanitize_record_for_json(record)
                        f.write(json.dumps(sanitized) + "\n")

                if gcs_bucket and gcs_storage_client:
                    bucket = gcs_storage_client.bucket(gcs_bucket)
                    blob_name = f"{gcs_prefix.strip('/')}/batch_{batch_count:05d}.jsonl"
                    blob = bucket.blob(blob_name)
                    blob.upload_from_filename(str(ndjson_path))

                    gcs_uri = f"gs://{gcs_bucket}/{blob_name}"
                    load_job = client.load_table_from_uri(
                        gcs_uri,
                        table_ref,
                        job_config=job_config,
                    )
                else:
                    with open(ndjson_path, "rb") as f:
                        load_job = client.load_table_from_file(
                            f,
                            table_ref,
                            job_config=job_config,
                        )

                load_job.result()  # Wait for batch load job to complete
                rows_uploaded += len(batch)

                # Immediately delete temporary batch file to prevent disk quota build-up
                if ndjson_path.exists():
                    ndjson_path.unlink()

                # Subsequent batches append to the created table
                if current_disposition == bigquery.WriteDisposition.WRITE_TRUNCATE:
                    job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND


                elapsed = time.time() - start_time
                rate = rows_uploaded / elapsed if elapsed > 0 else 0
                print(
                    f"\r  Uploaded {rows_uploaded:,}/{total_rows:,} rows "
                    f"({rows_uploaded / total_rows * 100:.1f}%) — {rate:.0f} rows/s",
                    end="",
                    flush=True,
                )

        elapsed_total = time.time() - start_time
        print(f"\nSuccessfully uploaded {rows_uploaded:,} rows to BigQuery table '{table_ref}' in {elapsed_total:.2f}s.")

        return {
            "status": "success",
            "rows_uploaded": rows_uploaded,
            "total_rows": total_rows,
            "elapsed_seconds": elapsed_total,
            "table_id": f"{client.project}.{dataset_id}.{table_name}",
        }
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload SQLite database tables (e.g. stories/db/stories.db) to Google BigQuery.",
    )
    parser.add_argument(
        "--db",
        default="stories/db/stories.db",
        help="Path to SQLite database file (default: stories/db/stories.db)",
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="Target BigQuery dataset ID",
    )
    parser.add_argument(
        "--table",
        default="stories",
        help="Target BigQuery table name (default: stories)",
    )
    parser.add_argument(
        "--project",
        default=None,
        help="GCP Project ID (default: active gcloud project)",
    )
    parser.add_argument(
        "--location",
        default="US",
        help="BigQuery location (default: US)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Number of rows per upload batch (default: {DEFAULT_BATCH_SIZE})",
    )
    parser.add_argument(
        "--gcs-bucket",
        default=None,
        help="Optional GCS bucket for staging upload files",
    )
    parser.add_argument(
        "--gcs-prefix",
        default="bq_stage",
        help="GCS object prefix when staging uploads (default: bq_stage)",
    )
    parser.add_argument(
        "--write-disposition",
        choices=["WRITE_TRUNCATE", "WRITE_APPEND", "WRITE_EMPTY"],
        default="WRITE_TRUNCATE",
        help="BigQuery write disposition (default: WRITE_TRUNCATE)",
    )
    parser.add_argument(
        "--max-bad-records",
        type=int,
        default=100,
        help="Maximum bad records allowed per batch (default: 100)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate schema and preview execution without uploading data",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of rows to upload (default: 0 for all rows)",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Row offset to start reading from SQLite (default: 0)",
    )

    args = parser.parse_args()

    # Fallback path if default stories/db/stories.db doesn't exist
    db_path = Path(args.db)
    if not db_path.exists() and args.db == "stories/db/stories.db" and Path("stories/stories.db").exists():
        db_path = Path("stories/stories.db")

    try:
        upload_sqlite_to_bigquery(
            db_path=db_path,
            dataset_id=args.dataset,
            table_name=args.table,
            project_id=args.project,
            location=args.location,
            batch_size=args.batch_size,
            gcs_bucket=args.gcs_bucket,
            gcs_prefix=args.gcs_prefix,
            write_disposition=args.write_disposition,
            max_bad_records=args.max_bad_records,
            dry_run=args.dry_run,
            limit=args.limit,
            offset=args.offset,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)




if __name__ == "__main__":
    main()
