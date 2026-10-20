import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.receipt_replay_store import (
    InMemoryReceiptReplayStore,
    SQLiteReceiptReplayStore,
)


class ReceiptReplayStoreTests(unittest.TestCase):
    def test_first_claim_is_accepted(self):
        result = InMemoryReceiptReplayStore().claim("booking-provider", "record-42", "hash-abc")
        self.assertTrue(result.accepted)

    def test_duplicate_claim_is_rejected(self):
        store = InMemoryReceiptReplayStore()
        first = store.claim("booking-provider", "record-42", "hash-abc")
        second = store.claim("booking-provider", "record-42", "hash-abc")
        self.assertTrue(first.accepted)
        self.assertFalse(second.accepted)
        self.assertIn("replay", second.reason.lower())

    def test_same_record_with_new_content_hash_is_distinct(self):
        store = InMemoryReceiptReplayStore()
        self.assertTrue(store.claim("booking-provider", "record-42", "hash-old").accepted)
        self.assertTrue(store.claim("booking-provider", "record-42", "hash-new").accepted)

    def test_missing_replay_key_fields_are_rejected(self):
        result = InMemoryReceiptReplayStore().claim("booking-provider", "record-42", "")
        self.assertFalse(result.accepted)

    def test_sqlite_claim_is_durable_across_store_recreation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "replay.sqlite3")
            first = SQLiteReceiptReplayStore(path)
            self.assertTrue(first.claim("booking-provider", "record-42", "hash-abc").accepted)
            recreated = SQLiteReceiptReplayStore(path)
            result = recreated.claim("booking-provider", "record-42", "hash-abc")
            self.assertFalse(result.accepted)
            self.assertIn("replay", result.reason.lower())

    def test_sqlite_claim_is_atomic_across_concurrent_connections(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "replay.sqlite3")
            SQLiteReceiptReplayStore(path)
            def claim_once(_):
                return SQLiteReceiptReplayStore(path).claim(
                    "booking-provider", "record-42", "hash-abc"
                ).accepted
            with ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(claim_once, range(16)))
            self.assertEqual(sum(results), 1)

    def test_sqlite_stores_distinct_hashes_as_distinct_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteReceiptReplayStore(str(Path(tmp) / "replay.sqlite3"))
            self.assertTrue(store.claim("booking-provider", "record-42", "hash-old").accepted)
            self.assertTrue(store.claim("booking-provider", "record-42", "hash-new").accepted)

    def test_sqlite_missing_key_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteReceiptReplayStore(str(Path(tmp) / "replay.sqlite3"))
            result = store.claim("booking-provider", "record-42", "")
            self.assertFalse(result.accepted)


if __name__ == "__main__":
    unittest.main()
