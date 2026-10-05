import unittest

from src.continuous_intelligence_orchestrator import ContinuousIntelligenceOrchestrator
from src.decision_command_bridge import DecisionCommandBridge
from src.decision_queue import DecisionQueue
from src.governed_decision_orchestrator import GovernedDecisionOrchestrator
from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge
from src.execution_telemetry import ExecutionTelemetry, ExecutionTelemetryCollector
from src.telemetry_signal_engine import IntelligenceSignal


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
