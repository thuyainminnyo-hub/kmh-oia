"""Restart integration test for trusted learning memory and proposal durability.

This test intentionally reuses the service's existing deterministic receipt,
decision, and classifier fixtures; it verifies the composition across both
persistence boundaries rather than claiming real-provider production evidence.
"""
import tempfile
import unittest
from pathlib import Path

from src.adaptation_proposal_repository import SQLiteAdaptationProposalRepository
from src.operating_memory import OperatingMemory
from src.trusted_decision_learning_service import TrustedDecisionLearningService
from test_trusted_decision_learning_service import TrustedDecisionLearningServiceTests


class TrustedLearningRestartIntegrationTests(unittest.TestCase):
    def test_memory_and_proposal_status_survive_service_reconstruction_and_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            memory_path = root / "learning-memory.json"
            proposal_path = root / "adaptation-proposals.sqlite3"

            fixtures = TrustedDecisionLearningServiceTests()
            fixtures.setUp()
            decision = fixtures.decision
            execution = fixtures.execution()
            classifier = fixtures.classifier
            adapter = fixtures.adapter

            first_service = TrustedDecisionLearningService(
                classifier=classifier,
                receipt_verifier=fixtures.verifier,
                memory=OperatingMemory(memory_path),
                adaptation_proposal_repository=SQLiteAdaptationProposalRepository(
                    str(proposal_path)
                ),
            )
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

            # Rebuild every persistence-facing service dependency as after restart.
            restarted_service = TrustedDecisionLearningService(
                classifier=classifier,
                receipt_verifier=fixtures.verifier,
                memory=OperatingMemory(memory_path),
                adaptation_proposal_repository=SQLiteAdaptationProposalRepository(
                    str(proposal_path)
                ),
            )
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
            self.assertEqual(adapter.calls, 2)


if __name__ == "__main__":
    unittest.main()
