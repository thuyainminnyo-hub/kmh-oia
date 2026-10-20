import tempfile
import unittest
from pathlib import Path

from src.receipt_replay_store import InMemoryReceiptReplayStore


class ReceiptReplayStoreTests(unittest.TestCase):
    def test_first_claim_is_accepted(self):
        store = InMemoryReceiptReplayStore()
        result = store.claim("booking-provider", "record-42", "hash-abc")
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
        first = store.claim("booking-provider", "record-42", "hash-old")
        second = store.claim("booking-provider", "record-42", "hash-new")
        self.assertTrue(first.accepted)
        self.assertTrue(second.accepted)

    def test_missing_replay_key_fields_are_rejected(self):
        store = InMemoryReceiptReplayStore()
        result = store.claim("booking-provider", "record-42", "")
        self.assertFalse(result.accepted)


if __name__ == "__main__":
    unittest.main()
