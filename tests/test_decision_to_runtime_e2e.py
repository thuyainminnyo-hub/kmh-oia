import unittest

from src.decision_command_bridge import DecisionCommandBridge
from src.decision_queue import DecisionQueue
from src.execution_telemetry import ExecutionTelemetryCollector
from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge
from src.telemetry_signal_engine import IntelligenceSignal, TelemetrySignalEngine


class DecisionToRuntimeE2ETests(unittest.TestCase):
    def test_approved_decision_reaches_runtime_and_produces_health_signal(self):
        queue = DecisionQueue()
        signal = IntelligenceSignal(
            "QUALITY_RISK", "HIGH", "qa_pass_rate", 0.50, 0.80,
            "QA pass rate is low.",
            "Review failed executions.",
        )
        decision = queue.enqueue(signal, owner="system")
        queue.decide(decision.id, approved=True)

        console = LiveOperatingConsole(
            date="2026-10-05",
            primary_objective="Decision to runtime loop",
        )
        applied = DecisionCommandBridge().apply(
            queue,
            console,
            decision.id,
            expected_output="quality review completed",
        )

        collector = ExecutionTelemetryCollector()
        record = LiveRuntimeBridge(
            console,
            telemetry_collector=collector,
        ).execute(applied.command_id)

        self.assertEqual(record.final_status, "LEARNED")
        self.assertEqual(record.source_decision_id, decision.id)
        self.assertTrue(record.telemetry.qa_passed)
        snapshot = collector.snapshot()
        self.assertEqual(snapshot.executions, 1)
        self.assertEqual(snapshot.evidence_coverage, 1.0)

        healthy_signals = TelemetrySignalEngine().analyze(snapshot)
        self.assertEqual(healthy_signals, [])

    def test_rejected_decision_never_reaches_runtime(self):
        queue = DecisionQueue()
        signal = IntelligenceSignal(
            "QUALITY_RISK", "HIGH", "qa_pass_rate", 0.50, 0.80,
            "QA pass rate is low.",
            "Review failed executions.",
        )
        decision = queue.enqueue(signal, owner="system")
        queue.decide(decision.id, approved=False)

        console = LiveOperatingConsole(
            date="2026-10-05",
            primary_objective="Rejected decision",
        )

        with self.assertRaises(ValueError):
            DecisionCommandBridge().apply(
                queue,
                console,
                decision.id,
                expected_output="quality review completed",
            )

        self.assertEqual(console.snapshot().commands, [])


if __name__ == "__main__":
    unittest.main()
