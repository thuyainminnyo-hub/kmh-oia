import tempfile
import unittest
from pathlib import Path

from src.learning_ledger import SQLiteLearningLedger


class LearningOutboxLeaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = SQLiteLearningLedger(str(Path(self.tmp.name) / "ledger.sqlite3"))
        self.ledger.record_learning(
            event_id="event:1",
            event={
                "command_id": "cmd:1", "wanted": "x", "did": "y",
                "actual": "y", "verified": "receipt", "decision": "d",
                "learned": "l", "changed": "c", "next_command": "n",
            },
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_only_one_worker_claims_a_pending_event(self):
        first = self.ledger.claim_pending(worker_id="worker-a", lease_seconds=60)
        second = self.ledger.claim_pending(worker_id="worker-b", lease_seconds=60)
        self.assertEqual(len(first), 1)
        self.assertEqual(second, ())
        self.assertEqual(first[0]["worker_id"], "worker-a")

    def test_expired_lease_can_be_reclaimed(self):
        first = self.ledger.claim_pending(worker_id="worker-a", lease_seconds=1)
        with self.ledger._connect() as connection:
            connection.execute(
                "UPDATE learning_outbox SET lease_until = 0 WHERE event_id = ?",
                ("event:1",),
            )
        second = self.ledger.claim_pending(worker_id="worker-b", lease_seconds=60)
        self.assertEqual(len(second), 1)
        self.assertNotEqual(first[0]["claim_token"], second[0]["claim_token"])

    def test_stale_claim_token_cannot_acknowledge_event(self):
        first = self.ledger.claim_pending(worker_id="worker-a", lease_seconds=60)
        with self.ledger._connect() as connection:
            connection.execute(
                "UPDATE learning_outbox SET lease_until = 0 WHERE event_id = ?",
                ("event:1",),
            )
        second = self.ledger.claim_pending(worker_id="worker-b", lease_seconds=60)
        with self.assertRaises(RuntimeError):
            self.ledger.mark_projected("event:1", claim_token=first[0]["claim_token"])
        self.ledger.mark_projected("event:1", claim_token=second[0]["claim_token"])
        self.assertEqual(self.ledger.pending_outbox(), ())

    def test_claim_validation(self):
        with self.assertRaises(ValueError):
            self.ledger.claim_pending(worker_id="", limit=1)
        with self.assertRaises(ValueError):
            self.ledger.claim_pending(worker_id="worker", lease_seconds=0)


if __name__ == "__main__":
    unittest.main()
