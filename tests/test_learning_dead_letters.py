import tempfile
import unittest
from pathlib import Path

from src.learning_ledger import SQLiteLearningLedger


class LearningDeadLetterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = SQLiteLearningLedger(str(Path(self.tmp.name) / "ledger.sqlite3"))
        self.ledger.record_learning(
            event_id="event:quarantine",
            event={
                "command_id": "cmd", "wanted": "x", "did": "y",
                "actual": "y", "verified": "receipt", "decision": "d",
                "learned": "l", "changed": "c", "next_command": "n",
            },
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_repeated_failures_quarantine_after_max_attempts(self):
        for attempt in range(3):
            claimed = self.ledger.claim_pending(worker_id=f"worker-{attempt}")
            self.assertEqual(len(claimed), 1)
            count = self.ledger.record_projection_failure(
                "event:quarantine",
                "ProjectionError: sink unavailable",
                claim_token=claimed[0]["claim_token"],
                max_attempts=3,
            )
            self.assertEqual(count, attempt + 1)
        self.assertEqual(self.ledger.pending_outbox(), ())
        dead = self.ledger.dead_letters()
        self.assertEqual(len(dead), 1)
        self.assertEqual(dead[0]["attempts"], 3)

    def test_manual_replay_requires_actor_and_reason_and_is_audited(self):
        claimed = self.ledger.claim_pending(worker_id="worker")
        self.ledger.record_projection_failure(
            "event:quarantine", "temporary failure",
            claim_token=claimed[0]["claim_token"], max_attempts=1,
        )
        with self.assertRaises(ValueError):
            self.ledger.replay_dead_letter("event:quarantine", actor="", reason="retry")
        self.ledger.replay_dead_letter(
            "event:quarantine", actor="operator:reviewer",
            reason="Sink repaired; replay approved",
        )
        self.assertEqual(len(self.ledger.pending_outbox()), 1)
        self.assertEqual(self.ledger.dead_letters(), ())
        with self.ledger._connect() as connection:
            rows = connection.execute(
                "SELECT event_id, actor, reason FROM learning_replay_audit"
            ).fetchall()
        self.assertEqual(rows, [(
            "event:quarantine", "operator:reviewer",
            "Sink repaired; replay approved",
        )])

    def test_retry_limit_validation(self):
        with self.assertRaises(ValueError):
            self.ledger.record_projection_failure(
                "event:quarantine", "error", max_attempts=0
            )


if __name__ == "__main__":
    unittest.main()
