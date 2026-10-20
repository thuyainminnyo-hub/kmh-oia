import unittest

from src.decision_command_bridge import DecisionCommandBridge
from src.decision_queue import DecisionQueue
from src.execution_telemetry import ExecutionTelemetryCollector
from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge
from src.telemetry_signal_engine import IntelligenceSignal, TelemetrySignalEngine


class DecisionToRuntimeE2ETests(unittest.TestCase):
    def _approved_command(self):
        queue = DecisionQueue()
        signal = IntelligenceSignal(
            "QUALITY_RISK", "HIGH", "qa_pass_rate", 0.50, 0.80,
            "QA pass rate is low.", "Review failed executions.",
        )
        decision = queue.enqueue(signal, owner="system")
        queue.decide(decision.id, approved=True)
        console = LiveOperatingConsole(
            date="2026-10-05", primary_objective="Decision to runtime loop",
        )
        applied = DecisionCommandBridge().apply(
            queue, console, decision.id,
            expected_output="quality review completed",
        )
        return decision, console, applied

    def test_approved_decision_reaches_runtime_and_keeps_learning_unadmitted_by_default(self):
        decision, console, applied = self._approved_command()
        collector = ExecutionTelemetryCollector()
        record = LiveRuntimeBridge(console, telemetry_collector=collector).execute(
            applied.command_id
        )

        self.assertEqual(record.final_status, "LEARNED")
        self.assertEqual(record.source_decision_id, decision.id)
        self.assertIsNotNone(record.operating_loop)
        self.assertTrue(record.operating_loop.decision_traceable)
        self.assertEqual(record.operating_loop.evidence_status, "OBSERVED")
        self.assertEqual(record.operating_loop.learning_status, "NOT_ADMITTED")
        self.assertFalse(record.operating_loop.externally_validated)
        self.assertIsNotNone(record.admission)
        self.assertFalse(record.admission.learning_admitted)
        self.assertIn("source", record.admission.missing_fields)
        self.assertIn("raw_observation", record.admission.missing_fields)
        self.assertTrue(any("missing" in reason.lower() for reason in record.admission.reasons))
        self.assertTrue(record.telemetry.qa_passed)

        snapshot = collector.snapshot()
        self.assertEqual(snapshot.executions, 1)
        self.assertEqual(snapshot.evidence_coverage, 1.0)
        self.assertEqual(TelemetrySignalEngine().analyze(snapshot), [])

    def test_outcome_linked_evidence_can_be_admitted_when_explicitly_supplied(self):
        decision, console, applied = self._approved_command()
        record = LiveRuntimeBridge(console).execute(
            applied.command_id,
            evidence_source="booking_system:record-42",
            raw_observation="booking_id=record-42",
            interpretation="booking attributed to execution",
            verification_status="OUTCOME_LINKED",
            outcome_linked=True,
            source_authenticated=True,
            attribution_verified=True,
        )
        self.assertFalse(record.admission.learning_admitted)
        self.assertEqual(record.operating_loop.evidence_status, "OUTCOME_LINKED")
        self.assertEqual(record.operating_loop.learning_status, "NOT_ADMITTED")
        self.assertFalse(record.operating_loop.externally_validated)
        self.assertEqual(record.admission.missing_fields, ())
        self.assertTrue(any("trusted source receipt" in reason.lower() for reason in record.admission.reasons))

    def test_outcome_link_flag_without_matching_status_stays_unadmitted(self):
        _, console, applied = self._approved_command()
        record = LiveRuntimeBridge(console).execute(
            applied.command_id,
            evidence_source="booking_system:record-42",
            raw_observation="booking_id=record-42",
            verification_status="VERIFIED",
            outcome_linked=True,
        )
        self.assertFalse(record.admission.learning_admitted)
        self.assertEqual(record.operating_loop.learning_status, "NOT_ADMITTED")

    def test_caller_claimed_outcome_link_without_authentication_is_blocked(self):
        _, console, applied = self._approved_command()
        record = LiveRuntimeBridge(console).execute(
            applied.command_id,
            evidence_source="booking_system:record-42",
            raw_observation="booking_id=record-42",
            verification_status="OUTCOME_LINKED",
            outcome_linked=True,
        )
        self.assertFalse(record.admission.learning_admitted)
        self.assertEqual(record.operating_loop.learning_status, "NOT_ADMITTED")
        self.assertTrue(any("authentication" in reason.lower() for reason in record.admission.reasons))

    def test_rejected_decision_never_reaches_runtime(self):
        queue = DecisionQueue()
        signal = IntelligenceSignal(
            "QUALITY_RISK", "HIGH", "qa_pass_rate", 0.50, 0.80,
            "QA pass rate is low.", "Review failed executions.",
        )
        decision = queue.enqueue(signal, owner="system")
        queue.decide(decision.id, approved=False)
        console = LiveOperatingConsole(
            date="2026-10-05", primary_objective="Rejected decision",
        )
        with self.assertRaises(ValueError):
            DecisionCommandBridge().apply(
                queue, console, decision.id,
                expected_output="quality review completed",
            )
        self.assertEqual(console.snapshot().commands, [])


if __name__ == "__main__":
    unittest.main()
