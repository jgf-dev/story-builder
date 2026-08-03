import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from storybuilder.downloader.bq_upload import (
    fetch_sqlite_rows_in_batches,
    get_sqlite_schema,
    map_sqlite_to_bq_schema,
    sanitize_record_for_json,
    upload_sqlite_to_bigquery,
)


class TestBQUpload(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_stories.db"
        self.conn = sqlite3.connect(str(self.db_path))

        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                title TEXT,
                char_count INTEGER,
                rating REAL,
                created_at DATETIME
            )
            """
        )
        cursor.executemany(
            "INSERT INTO stories (path, title, char_count, rating, created_at) VALUES (?, ?, ?, ?, ?)",
            [
                ("gay/romance/story1.txt", "Story One", 1000, 4.5, "2026-01-01 12:00:00"),
                ("gay/romance/story2.txt", "Story Two", 2500, 4.8, "2026-01-02 12:00:00"),
                ("gay/sci-fi/story3.txt", "Story Three", 3000, 4.2, "2026-01-03 12:00:00"),
            ],
        )
        self.conn.commit()

    def tearDown(self) -> None:
        self.conn.close()
        self.temp_dir.cleanup()

    def test_get_sqlite_schema(self) -> None:
        columns = get_sqlite_schema(self.conn, "stories")
        col_names = [c["name"] for c in columns]
        self.assertEqual(col_names, ["id", "path", "title", "char_count", "rating", "created_at"])
        col_types = {c["name"]: c["type"] for c in columns}
        self.assertEqual(col_types["id"], "INTEGER")
        self.assertEqual(col_types["title"], "TEXT")
        self.assertEqual(col_types["rating"], "REAL")

    def test_map_sqlite_to_bq_schema(self) -> None:
        columns = get_sqlite_schema(self.conn, "stories")
        bq_fields = map_sqlite_to_bq_schema(columns)
        field_dict = {f.name: f.field_type for f in bq_fields}
        self.assertEqual(field_dict["id"], "INT64")
        self.assertEqual(field_dict["path"], "STRING")
        self.assertEqual(field_dict["char_count"], "INT64")
        self.assertEqual(field_dict["rating"], "FLOAT64")
        self.assertEqual(field_dict["created_at"], "TIMESTAMP")

    def test_fetch_sqlite_rows_in_batches(self) -> None:
        cols = ["id", "path", "title"]
        batches = list(fetch_sqlite_rows_in_batches(self.conn, "stories", cols, batch_size=2))
        self.assertEqual(len(batches), 2)
        self.assertEqual(len(batches[0]), 2)
        self.assertEqual(len(batches[1]), 1)
        self.assertEqual(batches[0][0]["title"], "Story One")

    def test_fetch_sqlite_rows_in_batches_with_offset(self) -> None:
        cols = ["id", "path", "title"]
        batches = list(fetch_sqlite_rows_in_batches(self.conn, "stories", cols, batch_size=2, offset=1))
        self.assertEqual(len(batches), 1)
        self.assertEqual(len(batches[0]), 2)
        self.assertEqual(batches[0][0]["title"], "Story Two")


    def test_sanitize_record_for_json(self) -> None:
        rec = {"a": 1, "b": "hello", "c": None, "d": b"binary_data"}
        sanitized = sanitize_record_for_json(rec)
        self.assertEqual(sanitized["a"], 1)
        self.assertEqual(sanitized["b"], "hello")
        self.assertIsNone(sanitized["c"])
        self.assertEqual(sanitized["d"], "binary_data")

    def test_dry_run_upload(self) -> None:
        result = upload_sqlite_to_bigquery(
            db_path=self.db_path,
            dataset_id="test_dataset",
            table_name="stories",
            dry_run=True,
        )
        self.assertEqual(result["status"], "dry_run")
        self.assertEqual(result["total_rows"], 3)
        self.assertEqual(result["rows_uploaded"], 0)

    @patch("google.cloud.bigquery.Client")
    def test_mock_upload_bigquery(self, mock_bq_client_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.project = "test-project"
        mock_bq_client_cls.return_value = mock_client
        mock_load_job = MagicMock()
        mock_client.load_table_from_file.return_value = mock_load_job

        result = upload_sqlite_to_bigquery(
            db_path=self.db_path,
            dataset_id="test_dataset",
            table_name="stories",
            batch_size=2,
            dry_run=False,
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["rows_uploaded"], 3)
        self.assertEqual(mock_client.load_table_from_file.call_count, 2)

    @patch("google.cloud.storage.Client")
    @patch("google.cloud.bigquery.Client")
    def test_mock_upload_gcs_bigquery(
        self, mock_bq_client_cls: MagicMock, mock_gcs_client_cls: MagicMock
    ) -> None:
        mock_bq_client = MagicMock()
        mock_bq_client.project = "test-project"
        mock_bq_client_cls.return_value = mock_bq_client
        mock_load_job = MagicMock()
        mock_bq_client.load_table_from_uri.return_value = mock_load_job

        mock_gcs_client = MagicMock()
        mock_gcs_client_cls.return_value = mock_gcs_client

        result = upload_sqlite_to_bigquery(
            db_path=self.db_path,
            dataset_id="test_dataset",
            table_name="stories",
            batch_size=2,
            gcs_bucket="my_test_bucket",
            dry_run=False,
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["rows_uploaded"], 3)
        self.assertEqual(mock_bq_client.load_table_from_uri.call_count, 2)


if __name__ == "__main__":
    unittest.main()
