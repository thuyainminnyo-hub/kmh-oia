"""Composed trusted decision -> runtime execution -> learning admission integration test.

The deterministic adapter validates application wiring and attribution only. It
is not evidence of real-provider authenticity or production deployment.
"""
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from src.decision_queue import DecisionItem
from src.live_operating_console import LiveOperatingConsole
from src.trusted_decision_learning_service import TrustedOutcomeClassification
from src.trusted_learning_runtime import (
    TrustedLearningRuntimeConfig,
    build_trusted_learning_runtime,
)
from src.trusted_source_receipt import TrustedSourceReceipt


class DeterministicReceiptAdapter:
    provider_name = "booking-provider"

    def fetch_receipt(self, source_record_id, execution_id):
        return TrustedSourceReceipt(
            provider_name=self.provider_name,
            source_record_id=source_record_id,
            execution_id=execution_id,
            raw_observation="booking outcome=failed",
            observed_at=datetime.now(timezone.utc).isoformat(),
            content_hash="sha256:e2e-receipt-stable",
            verification_method="deterministic-test-adapter",
        )

    def verify_receipt(self, receipt):
        return (
            receipt.provider_name == self.provider_name
            and receipt.content_hash == "sha256:e2e-receipt-stable"
        )

    def match_execution(self, receipt, execution_id):
        return receipt.execution_id == execution_id


class FailedOutcomeClassifier:
    def classify(self, decision, execution, receipt):
        assert decision.id == execution.source_decision_id
        assert receipt.execution_id == execution.operating_loop.execution_id
        return TrustedOutcomeClassification(
            outcome_positive=False,
            reason="The deterministic test receipt reports a failed booking.",
            evidence_id="evidence:e2e-1",
        )


class TrustedDecisionLearningRuntimeIntegrationTests(unittest.TestCase):
    def test_approved_decision_executes_and_is_admitted_by_composed_learning_service(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision = DecisionItem(
                id="decision:e2e-1",
                signal_kind="QUALITY_RISK",
                severity="HIGH",
                problem="Verify booking outcome",
                recommended_action="Execute a bounded verification command",
                owner="test-owner",
                status="APPROVED",
            )
            console = LiveOperatingConsole(
                date="2026-10-28",
                primary_objective="Trusted decision to learning integration test",
            )
            command = console.add_command(
                "cmd:e2e-1",
                objective="Verify a deterministic booking outcome",
                priority="P1",
                owner="test-owner",
                expected_output="A runtime execution with linked trusted receipt",
                source_decision_id=decision.id,
                next_action="Review the governed adaptation proposal",
            )
            runtime = build_trusted_learning_runtime(
                console=console,
                config=TrustedLearningRuntimeConfig(
                    memory_path=str(root / "memory.json"),
                    proposal_sqlite_path=str(root / "proposals.sqlite3"),
                    replay_sqlite_path=str(root / "replay.sqlite3"),
                    allowed_source_providers=("booking-provider",),
                ),
                trusted_source_adapter=DeterministicReceiptAdapter(),
                classifier=FailedOutcomeClassifier(),
            )

            execution = runtime.bridge.execute(
                command.id,
                source_record_id="record:e2e-1",
                verification_status="OUTCOME_LINKED",
                outcome_linked=True,
            )

            self.assertEqual(execution.source_decision_id, decision.id)
            self.assertEqual(execution.command_id, command.id)
            self.assertIsNotNone(execution.operating_loop)
            execution_id = execution.operating_loop.execution_id
            self.assertTrue(execution_id)
            self.assertTrue(execution.admission.learning_admitted)
            self.assertEqual(execution.admission.evidence_status, "OUTCOME_LINKED")
            self.assertTrue(execution.trusted_receipt_verification.verified)
            self.assertEqual(execution.trusted_receipt_verification.execution_id, execution_id)
            self.assertEqual(execution.trusted_receipt_verification.source_record_id, "record:e2e-1")

            # The bridge's execution record reflects VERIFIED. Advance the governed
            # console lifecycle to LEARNED and pass that state to the learning gate.
            console.transition(command.id, "LEARNED")
            learning_execution = replace(execution, final_status="LEARNED")
            result = runtime.learning_service.capture_execution(
                decision,
                learning_execution,
                evidence_id="evidence:e2e-1",
                policy_version="policy:e2e-v1",
                next_command="Review the proposed adaptation",
            )

            self.assertTrue(result.admitted, result.reasons)
            self.assertEqual(result.execution_id, execution_id)
            self.assertEqual(result.memory.event_id, result.adaptation.id.removeprefix("adapt:"))
            self.assertEqual(result.adaptation.status, "PROPOSED")
            stored_proposal = runtime.proposal_repository.get(result.adaptation.id)
            self.assertIsNotNone(stored_proposal)
            self.assertEqual(stored_proposal["status"], "PROPOSED")
            self.assertEqual(stored_proposal["id"], result.adaptation.id)
            self.assertTrue(runtime.replay_store.health_check())

            # The bridge writes its execution event and learning writes a separate,
            # outcome-linked event; assert both exist without claiming cross-store atomicity.
            self.assertGreaterEqual(len(runtime.memory.recent(20)), 2)


if __name__ == "__main__":
    unittest.main()
