import unittest
from datetime import datetime, timezone

from src.continuous_intelligence_orchestrator import ContinuousIntelligenceOrchestrator
from src.decision_command_bridge import DecisionCommandBridge
from src.decision_queue import DecisionQueue
from src.governed_decision_orchestrator import GovernedDecisionOrchestrator
from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge
from src.execution_telemetry import ExecutionTelemetry, ExecutionTelemetryCollector
from src.operating_memory import OperatingMemory
from src.telemetry_signal_engine import IntelligenceSignal
from src.trusted_decision_learning_service import (
    TrustedDecisionLearningService,
    TrustedOutcomeClassification,
)
from src.trusted_source_receipt import TrustedSourceReceipt


class FakeBookingAdapter:
    provider_name = "booking-provider"

    def fetch_receipt(self, source_record_id, execution_id):
        return TrustedSourceReceipt(
            provider_name=self.provider_name,
            source_record_id=source_record_id,
            execution_id=execution_id,
            raw_observation="status=failed;reason=booking_not_completed",
            observed_at=datetime.now(timezone.utc).isoformat(),
            content_hash=f"sha256:{execution_id}",
            verification_method="test-provider-signature-and-attribution",
        )

    def verify_receipt(self, receipt):
        return receipt.content_hash.startswith("sha256:")

    def match_execution(self, receipt, execution_id):
        return receipt.execution_id == execution_id


class FakeOutcomeClassifier:
    def classify(self, decision, execution, receipt):
        return TrustedOutcomeClassification(
            outcome_positive=False,
            reason="Provider receipt indicates the booking outcome failed.",
            evidence_id="evidence:booking-outcome:1",
        )


class GovernedDecisionOrchestratorTests(unittest.TestCase):
    def signal(self):
        return IntelligenceSignal(
            "QUALITY_RISK", "HIGH", "qa_pass_rate", 0.5, 0.8,
            "QA is low.", "Review failed executions."
        )

    def test_approved_decision_reaches_runtime(self):
        queue = DecisionQueue()
        decision = queue.enqueue(self.signal(), owner="system")
        queue.decide(decision.id, approved=True)
        console = LiveOperatingConsole(
            date="2026-10-05",
            primary_objective="Governed execution",
        )
        telemetry = ExecutionTelemetryCollector()
        bridge = LiveRuntimeBridge(console, telemetry_collector=telemetry)
        result = GovernedDecisionOrchestrator(
            queue, console, runtime_bridge=bridge
        ).execute_approved(
            decision.id, expected_output="quality review completed"
        )

        self.assertEqual(result.execution.final_status, "LEARNED")
        self.assertEqual(result.execution.command_id, result.applied_decision.command_id)
        self.assertEqual(telemetry.snapshot().executions, 1)
        self.assertIsNone(result.learning_feedback)

    def test_verified_runtime_receipt_flows_to_governed_learning_candidate(self):
        queue = DecisionQueue()
        decision = queue.enqueue(self.signal(), owner="system")
        queue.decide(decision.id, approved=True)
        console = LiveOperatingConsole(
            date="2026-10-20",
            primary_objective="Governed execution with verified outcome",
        )
        memory = OperatingMemory()
        learning_service = TrustedDecisionLearningService(
            classifier=FakeOutcomeClassifier(),
            memory=memory,
        )
        runtime = LiveRuntimeBridge(
            console,
            trusted_source_adapter=FakeBookingAdapter(),
            allowed_source_providers=("booking-provider",),
        )
        result = GovernedDecisionOrchestrator(
            queue,
            console,
            runtime_bridge=runtime,
            learning_service=learning_service,
        ).execute_approved(
            decision.id,
            expected_output="quality review completed",
            source_record_id="booking:record:1",
            learning_evidence_id="evidence:booking-outcome:1",
            learning_policy_version="policy:v1",
            learning_next_command="Run a bounded shadow experiment",
        )

        self.assertEqual(result.execution.final_status, "LEARNED")
        self.assertTrue(result.execution.trusted_receipt_verification.verified)
        self.assertEqual(result.execution.admission.decision, "ADMITTED")
        self.assertIsNotNone(result.learning_feedback)
        self.assertTrue(result.learning_feedback.admitted)
        self.assertEqual(result.learning_feedback.outcome.quality, "POOR")
        self.assertEqual(result.learning_feedback.adaptation.status, "PROPOSED")
        self.assertEqual(len(memory.recent()), 1)

    def test_learning_service_with_missing_trusted_adapter_fails_closed(self):
        queue = DecisionQueue()
        decision = queue.enqueue(self.signal(), owner="system")
        queue.decide(decision.id, approved=True)
        console = LiveOperatingConsole(
            date="2026-10-20",
            primary_objective="Execution without trusted receipt adapter",
        )
        memory = OperatingMemory()
        learning_service = TrustedDecisionLearningService(
            classifier=FakeOutcomeClassifier(),
            memory=memory,
        )
        result = GovernedDecisionOrchestrator(
            queue,
            console,
            runtime_bridge=LiveRuntimeBridge(console),
            learning_service=learning_service,
        ).execute_approved(
            decision.id,
            expected_output="quality review completed",
            source_record_id="booking:record:missing",
            learning_evidence_id="evidence:booking-outcome:1",
            learning_policy_version="policy:v1",
            learning_next_command="Hold for verification",
        )
        self.assertFalse(result.learning_feedback.admitted)
        self.assertIsNone(result.learning_feedback.memory)
        self.assertIsNone(result.learning_feedback.adaptation)
        self.assertEqual(memory.recent(), ())

    def test_pending_decision_cannot_reach_runtime(self):
        queue = DecisionQueue()
        decision = queue.enqueue(self.signal(), owner="system")
        console = LiveOperatingConsole(date="2026-10-05")
        with self.assertRaises(PermissionError):
            GovernedDecisionOrchestrator(queue, console).execute_approved(
                decision.id, expected_output="quality review completed"
            )
        self.assertEqual(console.snapshot().commands, [])

    def test_rejected_decision_cannot_reach_runtime(self):
        queue = DecisionQueue()
        decision = queue.enqueue(self.signal(), owner="system")
        queue.decide(decision.id, approved=False)
        console = LiveOperatingConsole(date="2026-10-05")
        with self.assertRaises(PermissionError):
            GovernedDecisionOrchestrator(queue, console).execute_approved(
                decision.id, expected_output="quality review completed"
            )
        self.assertEqual(console.snapshot().commands, [])


if __name__ == "__main__":
    unittest.main()
