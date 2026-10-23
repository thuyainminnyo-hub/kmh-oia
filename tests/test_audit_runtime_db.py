import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.audit_runtime_db import audit_database


class ReadOnlyAuditTests(unittest.TestCase):
    def test_reports_schema_counts_without_returning_record_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "payments.sqlite3"
            with sqlite3.connect(path) as conn:
                conn.execute(
                    "CREATE TABLE payments (payment_id TEXT PRIMARY KEY, "
                    "student_name TEXT, status TEXT)"
                )
                conn.execute(
                    "INSERT INTO payments VALUES (?, ?, ?)",
                    ("private-payment-id", "Private Student Name", "pending"),
                )
                conn.execute(
                    "INSERT INTO payments VALUES (?, ?, ?)",
                    ("private-payment-id-2", "Another Private Name", "confirmed"),
                )

            report = audit_database(path)
            rendered = repr(report)
            self.assertEqual(report["payment_row_count"], 2)
            self.assertEqual(
                report["payment_status_counts"],
                {"confirmed": 1, "pending": 1},
            )
            self.assertFalse(report["tenant_id_column_present"])
            self.assertNotIn("Private Student Name", rendered)
            self.assertNotIn("private-payment-id", rendered)

            # The connection must be read-only: a write attempt fails.
            uri = path.resolve().as_uri() + "?mode=ro"
            with sqlite3.connect(uri, uri=True) as conn:
                conn.execute("PRAGMA query_only=ON")
                with self.assertRaises(sqlite3.OperationalError):
                    conn.execute("INSERT INTO payments VALUES ('x', 'y', 'z')")

    def test_missing_database_raises_instead_of_claiming_clean_slate(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.sqlite3"
            with self.assertRaises(FileNotFoundError):
                audit_database(missing)

    def test_missing_payments_table_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.sqlite3"
            with sqlite3.connect(path) as conn:
                conn.execute("CREATE TABLE unrelated (id INTEGER)")
            report = audit_database(path)
            self.assertFalse(report["payments_table_found"])
            self.assertIsNone(report["payment_row_count"])


if __name__ == "__main__":
    unittest.main()
