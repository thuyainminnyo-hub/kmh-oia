import unittest

from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge
from src.standardization_engine import OperatingStandard
from src.trusted_source_receipt import TrustedSourceReceipt
from src.verified_learning_admission import VerifiedLearningAdmission
from src.decision_outcome_evaluator import DecisionOutcome


class FakeAdmissionReceiptAdapter:
    provider_name = "booking-provider"

    def fetch_receipt(self, source_record_id, execution_id):
        return TrustedSourceReceipt(
            provider_name=self.provider_name,
            source_record_id=source_record_id,
            execution_id=execution_id,
            raw_observation="booking_id=42;status=confirmed",
            observed_at="2026-10-22T00:00:00Z",
            content_hash="sha256:integration-fixture",
            verification_method="fake-adapter-integration-test",
        )

    def verify_receipt(self, receipt):
        return receipt.content_hash == "sha256:integration-fixture"

    def match_execution(self, receipt, execution_id):
        return receipt.execution_id == execution_id


class LiveRuntimeBridgeTests(unittest.TestCase):
    def test_command_runs_through_runtime_and_becomes_learned(self) -> None:
        console = LiveOperatingConsole(
            date="2026-10-05",
            primary_objective="Execute today's highest-leverage command",
        )
        command = console.add_command(
            objective="hello operating intelligence",
            priority="P1",
            owner="Human + AI",
            expected_output="runtime response",
        )

        record = LiveRuntimeBridge(console).execute(command.id)

        self.assertEqual(record.final_status, "LEARNED")
        self.assertEqual(record.qa_status, "PASS")
        self.assertIn("input_gateway", record.trace_stages)
        self.assertIn("evaluation", record.trace_stages)
        self.assertTrue(any(item.startswith("trace_id=") for item in record.evidence))

    def test_runtime_receipt_gate_and_learning_admission_are_connected(self) -> None:
        console = LiveOperatingConsole(date="2026-10-22", primary_objective="Integration proof")
        command = console.add_command(
            objective="run receipt admission integration",
            priority="P1",
            owner="test",
            expected_output="verified receipt reaches the gate",
            source_decision_id="decision:integration",
        )
        bridge = LiveRuntimeBridge(
            console,
            trusted_source_adapter=FakeAdmissionReceiptAdapter(),
            allowed_source_providers=("booking-provider",),
        )
        record = bridge.execute(
            command.id,
            source_record_id="record:integration",
            verification_status="OUTCOME_LINKED",
            outcome_linked=True,
        )
        self.assertEqual(record.final_status, "LEARNED")
        self.assertTrue(record.trusted_receipt_verification.verified)
        self.assertTrue(record.admission.learning_admitted)
        self.assertEqual(
            record.admission.receipt_content_hash,
            record.trusted_receipt_verification.content_hash,
        )
        self.assertEqual(record.trusted_receipt_verification.execution_id, record.operating_loop.execution_id)

        outcome = DecisionOutcome(
            decision_id="decision:integration",
            command_id=command.id,
            outcome_positive=True,
            quality="GOOD",
            reason="Integration-test outcome; this fixture is not external business evidence.",
        )
        proof = VerifiedLearningAdmission.from_execution(
            outcome,
            record,
            evidence_id="evidence:integration-test",
            policy_version="policy:test-fixture",
        )
        self.assertEqual(proof.execution_id, record.operating_loop.execution_id)
        self.assertEqual(proof.receipt_content_hash, "sha256:integration-fixture")

    def test_runtime_rejected_receipt_does_not_admit_learning(self) -> None:
        console = LiveOperatingConsole(date="2026-10-22", primary_objective="Rejected receipt")
        command = console.add_command(
            objective="run rejected receipt integration",
            priority="P1",
            owner="test",
            expected_output="receipt rejected closed",
            source_decision_id="decision:rejected",
        )
        bridge = LiveRuntimeBridge(console)
        record = bridge.execute(
            command.id,
            source_record_id="record:missing-adapter",
            verification_status="OUTCOME_LINKED",
            outcome_linked=True,
        )
        self.assertIsNotNone(record.trusted_receipt_verification)
        self.assertFalse(record.trusted_receipt_verification.verified)
        self.assertFalse(record.admission.learning_admitted)
        outcome = DecisionOutcome(
            decision_id="decision:rejected",
            command_id=command.id,
            outcome_positive=True,
            quality="GOOD",
            reason="Test-only outcome; not externally verified.",
        )
        with self.assertRaisesRegex(ValueError, "evidence admission must be ADMITTED"):
            VerifiedLearningAdmission.from_execution(
                outcome,
                record,
                evidence_id="evidence:rejected-test",
                policy_version="policy:test-fixture",
            )

    def test_governed_execution_feeds_evidence_back_to_control_plane(self) -> None:
        console = LiveOperatingConsole(date="2026-10-05", primary_objective="Governed execution")
        command = console.add_command(
            objective="execute governed work",
            priority="P1",
            owner="system",
            expected_output="runtime response",
        )
        standard = OperatingStandard(
            "std:a:v1", "a", "Require evidence", "Higher quality", 1, "ACTIVE"
        )

        record = LiveRuntimeBridge(console).execute(
            command.id, standard=standard, applied_rule="Require evidence"
        )

        self.assertIsNotNone(record.standard_feedback)
        self.assertFalse(record.standard_feedback.drift.drifted)
        self.assertIsNone(record.standard_feedback.trigger)

    def test_unknown_command_is_rejected(self) -> None:
        console = LiveOperatingConsole(date="2026-10-05")
        bridge = LiveRuntimeBridge(console)

        with self.assertRaises(KeyError):
            bridge.execute("missing-command")


if __name__ == "__main__":
    unittest.main()
