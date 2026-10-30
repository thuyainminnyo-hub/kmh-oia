import tempfile
import unittest
from pathlib import Path

from src.learning_ledger import SQLiteLearningLedger
from src.learning_recovery_worker import LearningRecoveryWorker
from src.operating_memory import OperatingMemory
from src.adaptation_proposal_repository import SQLiteAdaptationProposalRepository


class LearningRecoveryWorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.ledger = SQLiteLearningLedger(str(root / "ledger.sqlite3"))
        self.memory = OperatingMemory(path=root / "memory.json")
        self.proposals = SQLiteAdaptationProposalRepository(str(root / "proposals.sqlite3"))

    def tearDown(self):
        self.tmp.cleanup()

    def add_event(self, suffix):
        self.ledger.record_learning(
            event_id=f"event:{suffix}",
            event={
                "command_id": f"cmd:{suffix}",
                "wanted": "expected",
                "did": "completed",
                "actual": "observed",
                "verified": "receipt verified",
                "decision": "decision",
                "learned": "outcome admitted",
                "changed": "no change",
                "next_command": "review",
                "confidence": 0.9,
            },
        )

    def test_startup_recovery_projects_pending_events(self):
        self.add_event("1")
        self.add_event("2")
        worker = LearningRecoveryWorker(
            ledger=self.ledger,
            memory=self.memory,
            proposal_repository=self.proposals,
            max_batch_size=1,
            max_batches=5,
        )
        result = worker.run_once()
        self.assertEqual(result.scanned, 2)
        self.assertEqual(result.projected, 2)
        self.assertEqual(result.failed, 0)
        self.assertEqual(result.remaining, 0)
        self.assertTrue(result.healthy)
        self.assertIsNotNone(result.observability)
        self.assertEqual(result.observability["pending_events"], 0)
        self.assertEqual(result.observability["projected_events"], 2)
        self.assertEqual(result.observability["dead_letter_events"], 0)
        self.assertTrue(result.observability["ledger_healthy"])
        self.assertEqual(len(self.memory.recent(10)), 2)

    def test_worker_is_idempotent_when_no_pending_records(self):
        worker = LearningRecoveryWorker(
            ledger=self.ledger,
            memory=self.memory,
            proposal_repository=self.proposals,
        )
        result = worker.run_once()
        self.assertEqual(result.scanned, 0)
        self.assertEqual(result.projected, 0)
        self.assertEqual(result.remaining, 0)
        self.assertTrue(result.healthy)
        self.assertEqual(result.observability["pending_events"], 0)
        self.assertEqual(result.observability["projected_events"], 0)

    def test_worker_stops_after_projection_failure(self):
        self.add_event("1")

        class BrokenMemory:
            def record(self, **kwargs):
                raise RuntimeError("simulated sink failure")

        worker = LearningRecoveryWorker(
            ledger=self.ledger,
            memory=BrokenMemory(),
            proposal_repository=self.proposals,
        )
        result = worker.run_once()
        self.assertEqual(result.failed, 1)
        self.assertEqual(result.remaining, 1)
        self.assertFalse(result.healthy)
        self.assertEqual(result.observability["pending_events"], 1)
        self.assertEqual(result.observability["retry_attempts_total"], 1)

    def test_invalid_batch_limits_rejected(self):
        with self.assertRaises(ValueError):
            LearningRecoveryWorker(
                ledger=self.ledger,
                memory=self.memory,
                proposal_repository=self.proposals,
                max_batch_size=0,
            )


if __name__ == "__main__":
    unittest.main()
