import unittest
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from src.continuous_intelligence_orchestrator import ContinuousIntelligenceOrchestrator
from src.decision_command_bridge import DecisionCommandBridge
from src.decision_queue import DecisionQueue
from src.governed_decision_orchestrator import GovernedDecisionOrchestrator
from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import ExecutionRecord, LiveRuntimeBridge
from src.execution_telemetry import ExecutionTelemetry, ExecutionTelemetryCollector
from src.operating_memory import OperatingMemory
from src.telemetry_signal_engine import IntelligenceSignal
from src.trusted_decision_learning_service import (
    TrustedDecisionLearningService,
    TrustedOutcomeClassification,
)
from src.trusted_source_receipt import TrustedSourceReceipt
from src.receipt_replay_store import SQLiteReceiptReplayStore


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
        runtime = LiveRuntimeBridge(
            console,
            trusted_source_adapter=FakeBookingAdapter(),
            allowed_source_providers=("booking-provider",),
        )
        learning_service = TrustedDecisionLearningService(
            classifier=FakeOutcomeClassifier(),
            receipt_verifier=runtime.trusted_source_verifier,
            memory=memory,
        )
        result = GovernedDecisionOrchestrator(
            queue, console, runtime_bridge=runtime, learning_service=learning_service
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
        self.assertTrue(result.learning_feedback.admitted)
        self.assertEqual(result.learning_feedback.outcome.quality, "POOR")
        self.assertEqual(result.learning_feedback.adaptation.status, "PROPOSED")
        self.assertEqual(len(memory.recent()), 1)
        # Even the fully admitted end-to-end path creates a proposal only;
        # application is still blocked until a separate approval is recorded.
        with self.assertRaisesRegex(ValueError, "only approved adaptations can be applied"):
            learning_service._adaptation_engine.apply(result.learning_feedback.adaptation)
        self.assertEqual(result.learning_feedback.adaptation.status, "PROPOSED")

    def test_invalid_runtime_admission_provenance_blocks_learning_service(self):
        class MismatchedProvenanceAdapter(FakeBookingAdapter):
            def __init__(self):
                self.fetch_count = 0

            def fetch_receipt(self, source_record_id, execution_id):
                self.fetch_count += 1
                return TrustedSourceReceipt(
                    provider_name=self.provider_name,
                    source_record_id=source_record_id,
                    execution_id=execution_id,
                    raw_observation=(
                        "status=failed;reason=booking_not_completed"
                        if self.fetch_count == 1
                        else "different observation on learning re-check"
                    ),
                    observed_at=datetime.now(timezone.utc).isoformat(),
                    content_hash=f"sha256:{execution_id}",
                    verification_method="test-provider-signature-and-attribution",
                )

        queue = DecisionQueue()
        decision = queue.enqueue(self.signal(), owner="system")
        queue.decide(decision.id, approved=True)
        console = LiveOperatingConsole(
            date="2026-10-21",
            primary_objective="Provenance mismatch end-to-end",
        )
        memory = OperatingMemory()
        runtime = LiveRuntimeBridge(
            console,
            trusted_source_adapter=MismatchedProvenanceAdapter(),
            allowed_source_providers=("booking-provider",),
        )
        service = TrustedDecisionLearningService(
            classifier=FakeOutcomeClassifier(),
            receipt_verifier=runtime.trusted_source_verifier,
            memory=memory,
        )
        result = GovernedDecisionOrchestrator(
            queue, console, runtime_bridge=runtime, learning_service=service
        ).execute_approved(
            decision.id,
            expected_output="quality review completed",
            source_record_id="booking:record:mismatch",
            learning_evidence_id="evidence:booking-outcome:1",
            learning_policy_version="policy:v1",
            learning_next_command="Hold for evidence review",
        )

        self.assertTrue(result.execution.trusted_receipt_verification.verified)
        self.assertEqual(result.execution.admission.decision, "ADMITTED")
        self.assertFalse(result.learning_feedback.admitted)
        self.assertIsNone(result.learning_feedback.memory)
        self.assertIsNone(result.learning_feedback.adaptation)
        self.assertEqual(memory.recent(), ())
        self.assertEqual(result.learning_feedback.reasons, (
            "Independently verified receipt does not match runtime receipt.",
        ))

    def test_durable_replay_guard_is_shared_by_runtime_and_learning_boundary(self):
        queue = DecisionQueue()
        decision = queue.enqueue(self.signal(), owner="system")
        queue.decide(decision.id, approved=True)
        console = LiveOperatingConsole(
            date="2026-10-21",
            primary_objective="Durable replay guard end-to-end",
        )
        memory = OperatingMemory()
        with tempfile.TemporaryDirectory() as tmp:
            replay_store = SQLiteReceiptReplayStore(str(Path(tmp) / "replay.sqlite3"))
            runtime = LiveRuntimeBridge(
                console,
                trusted_source_adapter=FakeBookingAdapter(),
                allowed_source_providers=("booking-provider",),
                receipt_replay_store=replay_store,
                require_durable_replay_store=True,
            )
            learning_service = TrustedDecisionLearningService(
                classifier=FakeOutcomeClassifier(),
                receipt_verifier=runtime.trusted_source_verifier,
                memory=memory,
            )
            result = GovernedDecisionOrchestrator(
                queue, console, runtime_bridge=runtime, learning_service=learning_service
            ).execute_approved(
                decision.id,
                expected_output="quality review completed",
                source_record_id="booking:record:durable",
                learning_evidence_id="evidence:booking-outcome:1",
                learning_policy_version="policy:v1",
                learning_next_command="Run a bounded shadow experiment",
            )

            self.assertTrue(replay_store.health_check())
            self.assertIsNotNone(result.execution.trusted_receipt_verification)
            self.assertTrue(result.execution.trusted_receipt_verification.verified)
            self.assertTrue(result.learning_feedback.admitted)
            self.assertEqual(result.learning_feedback.outcome.quality, "POOR")
            self.assertEqual(len(memory.recent()), 1)
            # The learning boundary re-checks the exact receipt but must not
            # claim the replay key a second time: a subsequent execution-level
            # claim for that same provider/source/hash must be rejected.
            duplicate = replay_store.claim(
                "booking-provider", "booking:record:durable", "sha256:exec:"
                + result.execution.operating_loop.execution_id.removeprefix("exec:")
            )
            self.assertFalse(duplicate.accepted)

    def test_missing_runtime_verifier_fails_closed(self):
        queue = DecisionQueue()
        decision = queue.enqueue(self.signal(), owner="system")
        queue.decide(decision.id, approved=True)
        console = LiveOperatingConsole(
            date="2026-10-20",
            primary_objective="Execution without trusted provider adapter",
        )
        runtime = LiveRuntimeBridge(console)
        memory = OperatingMemory()
        learning_service = TrustedDecisionLearningService(
            classifier=FakeOutcomeClassifier(),
            receipt_verifier=runtime.trusted_source_verifier,
            memory=memory,
        )
        result = GovernedDecisionOrchestrator(
            queue, console, runtime_bridge=runtime, learning_service=learning_service
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

    def test_caller_outcome_boolean_is_not_forwarded_on_trusted_learning_path(self):
        class RecordingRuntimeBridge:
            def __init__(self):
                self.kwargs = None

            def execute(self, command_id, **kwargs):
                self.kwargs = kwargs
                return ExecutionRecord(
                    command_id=command_id,
                    response="runtime completed",
                    trace_stages=("input_gateway", "evaluation"),
                    evidence=("trace_id=trace:1",),
                    qa_status="PASS",
                    final_status="LEARNED",
                )

        queue = DecisionQueue()
        decision = queue.enqueue(self.signal(), owner="system")
        queue.decide(decision.id, approved=True)
        console = LiveOperatingConsole(date="2026-10-20")
        runtime = RecordingRuntimeBridge()
        learning_service = TrustedDecisionLearningService(
            classifier=FakeOutcomeClassifier(),
            receipt_verifier=None,
            memory=OperatingMemory(),
        )
        result = GovernedDecisionOrchestrator(
            queue, console, runtime_bridge=runtime, learning_service=learning_service
        ).execute_approved(
            decision.id,
            expected_output="quality review completed",
            outcome_positive=True,
            observed_effect=1.0,
            source_record_id="booking:record:1",
            learning_evidence_id="evidence:booking-outcome:1",
            learning_policy_version="policy:v1",
            learning_next_command="Hold for verification",
        )

        self.assertIsNone(runtime.kwargs["outcome_positive"])
        self.assertIsNone(runtime.kwargs["observed_effect"])
        self.assertFalse(result.learning_feedback.admitted)

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
