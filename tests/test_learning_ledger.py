import tempfile
import unittest
from pathlib import Path

from src.learning_ledger import LearningLedgerConflict, SQLiteLearningLedger


class SQLiteLearningLedgerTests(unittest.TestCase):
    def setUp(self):
        self.event_id = "learning:event-1"
        self.event = {
            "command_id": "cmd:1",
            "execution_id": "exec:1",
            "evidence_id": "evidence:1",
            "quality": "POOR",
        }
        self.proposal_id = "adapt:learning:event-1"
        self.proposal = {
            "source_command_id": "cmd:1",
            "problem": "outcome failed",
            "proposed_change": "review policy",
            "status": "PROPOSED",
        }

    def make_ledger(self, root):
        return SQLiteLearningLedger(str(Path(root) / "learning.sqlite3"))

    def test_event_proposal_and_outbox_are_created_as_one_durable_unit(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = self.make_ledger(tmp)
            result = ledger.record_learning(
                event_id=self.event_id,
                event=self.event,
                proposal_id=self.proposal_id,
                proposal=self.proposal,
            )
            self.assertEqual(result["event"], self.event)
            self.assertEqual(result["proposal_id"], self.proposal_id)
            self.assertEqual(result["proposal"], self.proposal)
            self.assertEqual(result["outbox_state"], "PENDING")
            self.assertEqual(len(ledger.pending_outbox()), 1)
            self.assertTrue(ledger.health_check())

            reopened = self.make_ledger(tmp)
            self.assertEqual(reopened.get_event(self.event_id), self.event)
            self.assertEqual(len(reopened.pending_outbox()), 1)

    def test_exact_retry_is_idempotent_and_does_not_duplicate_outbox(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = self.make_ledger(tmp)
            first = ledger.record_learning(
                event_id=self.event_id, event=self.event,
                proposal_id=self.proposal_id, proposal=self.proposal,
            )
            second = ledger.record_learning(
                event_id=self.event_id, event=self.event,
                proposal_id=self.proposal_id, proposal=self.proposal,
            )
            self.assertEqual(first, second)
            self.assertEqual(len(ledger.pending_outbox()), 1)

    def test_event_identity_reuse_with_changed_payload_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = self.make_ledger(tmp)
            ledger.record_learning(event_id=self.event_id, event=self.event)
            changed = dict(self.event, quality="GOOD")
            with self.assertRaises(LearningLedgerConflict):
                ledger.record_learning(event_id=self.event_id, event=changed)
            self.assertEqual(ledger.get_event(self.event_id), self.event)
            self.assertEqual(len(ledger.pending_outbox()), 1)

    def test_proposal_collision_rolls_back_new_event_and_outbox(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = self.make_ledger(tmp)
            ledger.record_learning(
                event_id="learning:original", event={"value": "original"},
                proposal_id=self.proposal_id, proposal=self.proposal,
            )
            with self.assertRaises(LearningLedgerConflict):
                ledger.record_learning(
                    event_id="learning:second", event={"value": "second"},
                    proposal_id=self.proposal_id,
                    proposal=dict(self.proposal, problem="different immutable payload"),
                )
            self.assertIsNone(ledger.get_event("learning:second"))
            self.assertEqual(len(ledger.pending_outbox()), 1)

    def test_outbox_failure_is_retryable_and_projection_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = self.make_ledger(tmp)
            ledger.record_learning(event_id=self.event_id, event=self.event)
            ledger.record_projection_failure(self.event_id, "JSON file temporarily unavailable")
            pending = ledger.pending_outbox()
            self.assertEqual(pending[0]["attempts"], 1)
            ledger.mark_projected(self.event_id)
            ledger.mark_projected(self.event_id)
            self.assertEqual(ledger.pending_outbox(), ())

    def test_invalid_outbox_limits_and_missing_events_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = self.make_ledger(tmp)
            with self.assertRaises(ValueError):
                ledger.pending_outbox(0)
            with self.assertRaises(ValueError):
                ledger.mark_projected("missing:event")


if __name__ == "__main__":
    unittest.main()
