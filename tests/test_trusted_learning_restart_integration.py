""""Restart integration tests for trusted learning persistence and recovery.

These tests use deterministic provider fixtures. They verify repository-level
recovery behavior, not real-provider authenticity or production deployment.
"""
import tempfile
import unittest
from pathlib import Path

from src.adaptation_proposal_repository import SQLiteAdaptationProposalRepository
from src.operating_memory import OperatingMemory
from src.trusted_decision_learning_service import TrustedDecisionLearningService
from test_trusted_decision_learning_service import TrustedDecisionLearningServiceTests


class TrustedLearningRestartIntegrationTests(unittest.TestCase):
    def _service(self, fixtures, memory_path, proposal_path):
        return TrustedDecisionLearningService(
            classifier=fixtures.classifier,
            receipt_verifier=fixtures.verifier,
            memory=OperatingMemory(memory_path),
            adaptation_proposal_repository=SQLiteAdaptationProposalRepository(
                str(proposal_path)
            ),
        )

    def test_memory_and_proposal_status_survive_service_reconstruction_and_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            memory_path = root / "learning-memory.json"
            proposal_path = root / "adaptation-proposals.sqlite3"

            fixtures = TrustedDecisionLearningServiceTests()
            fixtures.setUp()
            decision = fixtures.decision
            execution = fixtures.execution()
            first_service = self._service(fixtures, memory_path, proposal_path)
            first = first_service.capture_execution(
                decision,
                execution,
                evidence_id="evidence:1",
                policy_version="policy:v1",
                next_command="Run a bounded shadow experiment",
            )

            self.assertTrue(first.admitted)
            self.assertIsNotNone(first.memory)
            self.assertIsNotNone(first.adaptation)
            self.assertEqual(first.adaptation.status, "PROPOSED")

            approved = first_service._adaptation_engine.approve(first.adaptation)
            self.assertEqual(approved.status, "APPROVED")

            restarted_service = self._service(fixtures, memory_path, proposal_path)
            replayed = restarted_service.capture_execution(
                decision,
                execution,
                evidence_id="evidence:1",
                policy_version="policy:v1",
                next_command="Run a bounded shadow experiment",
            )

            restored_memory = OperatingMemory(memory_path)
            self.assertTrue(replayed.admitted)
            self.assertEqual(len(restored_memory.recent(10)), 1)
            self.assertEqual(replayed.memory.event_id, first.memory.event_id)
            self.assertEqual(replayed.adaptation.id, first.adaptation.id)
            self.assertEqual(replayed.adaptation.status, "APPROVED")
            self.assertEqual(replayed.adaptation.status, approved.status)
            self.assertEqual(fixtures.adapter.calls, 2)

    def test_retry_recovers_when_proposal_persistence_fails_after_memory_write(self):
        """A retry should complete a proposal after a crash-like partial failure."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            memory_path = root / "learning-memory.json"
            proposal_path = root / "adaptation-proposals.sqlite3"

            fixtures = TrustedDecisionLearningServiceTests()
            fixtures.setUp()
            decision = fixtures.decision
            execution = fixtures.execution()

            failing_repository = SQLiteAdaptationProposalRepository(str(proposal_path))

            def fail_before_proposal_commit(*args, **kwargs):
                raise OSError("simulated proposal-store outage")

            # Inject a failure after the service has recorded memory but before
            # the proposal repository can persist the adaptation proposal.
            failing_repository.get_or_create = fail_before_proposal_commit
            first_service = TrustedDecisionLearningService(
                classifier=fixtures.classifier,
                receipt_verifier=fixtures.verifier,
                memory=OperatingMemory(memory_path),
                adaptation_proposal_repository=failing_repository,
            )
            with self.assertRaisesRegex(OSError, "simulated proposal-store outage"):
                first_service.capture_execution(
                    decision,
                    execution,
                    evidence_id="evidence:1",
                    policy_version="policy:v1",
                    next_command="Run a bounded shadow experiment",
                )

            # Reconstruct the service and both persistence-facing stores as after restart.
            restarted_service = self._service(fixtures, memory_path, proposal_path)
            retried = restarted_service.capture_execution(
                decision,
                execution,
                evidence_id="evidence:1",
                policy_version="policy:v1",
                next_command="Run a bounded shadow experiment",
            )

            restored_memory = OperatingMemory(memory_path)
            self.assertTrue(retried.admitted)
            self.assertIsNotNone(retried.adaptation)
            self.assertEqual(retried.adaptation.status, "PROPOSED")
            self.assertEqual(len(restored_memory.recent(10)), 1)
            self.assertEqual(restored_memory.recent(10)[0].event_id, retried.memory.event_id)
            self.assertEqual(fixtures.adapter.calls, 2)


if __name__ == "__main__":
    unittest.main()
