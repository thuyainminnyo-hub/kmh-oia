import tempfile
import unittest
from pathlib import Path

from src.adaptation_proposal_repository import SQLiteAdaptationProposalRepository
from src.learning_ledger import SQLiteLearningLedger
from src.learning_outbox_projector import LearningOutboxProjector
from src.operating_memory import OperatingMemory


class FailOnce:
    def __init__(self, wrapped):
        self.wrapped = wrapped
        self.failed = False

    def get_or_create(self, proposal, idempotency_key):
        if not self.failed:
            self.failed = True
            raise RuntimeError("simulated interruption")
        return self.wrapped.get_or_create(proposal, idempotency_key)


class LearningOutboxProjectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.ledger = SQLiteLearningLedger(str(root / "ledger.sqlite3"))
        self.memory_path = root / "memory.json"
        self.memory = OperatingMemory(self.memory_path)
        self.proposals = SQLiteAdaptationProposalRepository(str(root / "proposals.sqlite3"))
        self.event_id = "learning:projector-1"
        self.proposal_id = "adapt:projector-1"
        self.event = {
            "command_id": "cmd:1", "wanted": "safe result",
            "did": "execute pilot", "actual": "partial result",
            "verified": "fixture evidence", "decision": "HOLD",
            "learned": "retry safely", "changed": "add recovery",
            "next_command": "rerun validation", "confidence": 0.8,
        }
        self.proposal = {
            "source_command_id": "cmd:1", "problem": "partial result",
            "proposed_change": "add recovery", "status": "PROPOSED",
        }
        self.ledger.record_learning(
            event_id=self.event_id, event=self.event,
            proposal_id=self.proposal_id, proposal=self.proposal,
        )

    def tearDown(self):
        self.temp.cleanup()

    def make_projector(self, repository=None, memory=None):
        return LearningOutboxProjector(
            ledger=self.ledger, memory=memory or self.memory,
            proposal_repository=repository or self.proposals,
        )

    def test_projects_both_sinks_before_acknowledging(self):
        result = self.make_projector().run_once()
        self.assertEqual((result.scanned, result.projected, result.failed), (1, 1, 0))
        self.assertEqual(self.memory.recent()[0].event_id, self.event_id)
        self.assertEqual(self.proposals.get(self.proposal_id)["id"], self.proposal_id)
        self.assertEqual(self.ledger.pending_outbox(), ())

    def test_partial_failure_recovers_after_restart_without_duplicate_memory(self):
        first = self.make_projector(FailOnce(self.proposals)).run_once()
        self.assertEqual((first.projected, first.failed), (0, 1))
        self.assertEqual(len(self.memory.recent(10)), 1)
        reopened = OperatingMemory(self.memory_path)
        second = self.make_projector(self.proposals, reopened).run_once()
        self.assertEqual((second.projected, second.failed), (1, 0))
        self.assertEqual(len(reopened.recent(10)), 1)
        self.assertEqual(self.ledger.pending_outbox(), ())


if __name__ == "__main__":
    unittest.main()
