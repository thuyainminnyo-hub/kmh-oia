import tempfile
import time
import unittest
from pathlib import Path

from src.learning_ledger import SQLiteLearningLedger
from src.learning_pipeline_observability import LearningPipelineObservability


class LearningPipelineObservabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = SQLiteLearningLedger(str(Path(self.tmp.name) / "ledger.sqlite3"))
        self.observer = LearningPipelineObservability(ledger=self.ledger)

    def tearDown(self):
        self.tmp.cleanup()

    def _record(self, event_id):
        self.ledger.record_learning(
            event_id=event_id,
            event={
                "command_id": event_id, "wanted": "x", "did": "y",
                "actual": "y", "verified": "receipt", "decision": "d",
                "learned": "l", "changed": "c", "next_command": "n",
            },
        )

    def test_empty_snapshot_is_healthy_and_has_no_oldest_age(self):
        snapshot = self.observer.snapshot()
        self.assertEqual(snapshot.total_events, 0)
        self.assertEqual(snapshot.pending_events, 0)
        self.assertIsNone(snapshot.oldest_pending_age_seconds)
        self.assertTrue(snapshot.ledger_healthy)

    def test_snapshot_counts_pending_active_expired_projected_and_dead_letters(self):
        self._record("pending-active")
        self._record("pending-expired")
        self._record("pending-unleased")
        self._record("projected")
        active = self.ledger.claim_pending(
            worker_id="active-worker", limit=1, lease_seconds=120
        )
        expired = self.ledger.claim_pending(
            worker_id="expired-worker", limit=1, lease_seconds=1
        )
        self.assertEqual(len(active), 1)
        self.assertEqual(len(expired), 1)
        self.ledger.mark_projected("projected")
        dead = self.ledger.claim_pending(worker_id="dead-worker", limit=1)
        self.assertEqual(len(dead), 1)
        self.ledger.record_projection_failure(
            dead[0]["event_id"], "sink unavailable",
            claim_token=dead[0]["claim_token"], max_attempts=1,
        )
        # Expire the second claim deterministically without sleeping.
        with self.ledger._connect() as connection:
            connection.execute(
                "UPDATE learning_outbox SET lease_until = 1 WHERE event_id = ?",
                (expired[0]["event_id"],),
            )
        snapshot = self.observer.snapshot(now_epoch=time.time() + 2)
        self.assertEqual(snapshot.total_events, 4)
        self.assertEqual(snapshot.pending_events, 2)
        self.assertEqual(snapshot.projected_events, 1)
        self.assertEqual(snapshot.dead_letter_events, 1)
        self.assertEqual(snapshot.active_leases, 1)
        self.assertEqual(snapshot.expired_leases, 1)
        self.assertEqual(snapshot.unleased_pending_events, 0)
        self.assertGreaterEqual(snapshot.retry_attempts_total, 2)

    def test_snapshot_does_not_mutate_queue_state(self):
        self._record("read-only")
        before = self.ledger.pending_outbox()
        self.observer.snapshot()
        after = self.ledger.pending_outbox()
        self.assertEqual(before, after)

    def test_invalid_clock_is_rejected(self):
        with self.assertRaises(ValueError):
            self.observer.snapshot(now_epoch=True)


if __name__ == "__main__":
    unittest.main()
