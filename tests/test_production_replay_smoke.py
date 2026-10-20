import tempfile
import unittest
from pathlib import Path

from scripts.production_replay_smoke import smoke_test
from src.receipt_replay_store import SQLiteReceiptReplayStore


class ProductionReplaySmokeTests(unittest.TestCase):
    def test_smoke_test_passes_when_database_file_exists_and_blocks_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "target-volume-fixture.sqlite3"
            # Initialize the database file as the operator must do on target.
            store = SQLiteReceiptReplayStore(str(db_path))
            self.assertTrue(store.health_check())
            result = smoke_test(db_path)
            self.assertEqual(result["result"], "PASS")
            self.assertEqual(
                result["test"],
                "sqlite_replay_across_independent_os_processes",
            )
            self.assertFalse(result["second_process"]["accepted"])
            self.assertIn("replay", str(result["second_process"]["reason"]).lower())

    def test_smoke_test_refuses_to_create_database_on_missing_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing_path = Path(tmp) / "not-created.sqlite3"
            with self.assertRaisesRegex(FileNotFoundError, "must already exist"):
                smoke_test(missing_path)
            self.assertFalse(missing_path.exists())


if __name__ == "__main__":
    unittest.main()
