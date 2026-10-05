import unittest

from src.continuous_intelligence_orchestrator import ContinuousIntelligenceOrchestrator
from src.execution_telemetry import ExecutionTelemetry, ExecutionTelemetryCollector


class ContinuousIntelligenceOrchestratorTests(unittest.TestCase):
    def test_healthy_cycle_produces_no_decisions(self):
        telemetry = ExecutionTelemetryCollector()
        telemetry.record(ExecutionTelemetry("cmd:1", True, False, False, 3, True, False, False, None))
        orchestrator = ContinuousIntelligenceOrchestrator(telemetry=telemetry)
        cycle = orchestrator.cycle()
        self.assertEqual(cycle.signals, ())
        self.assertEqual(cycle.ingested, ())
        self.assertEqual(orchestrator.decision_queue.pending(), [])

    def test_unhealthy_cycle_creates_pending_decisions(self):
        telemetry = ExecutionTelemetryCollector()
        telemetry.record(ExecutionTelemetry("cmd:1", False, True, True, 0, False, True, True, "REVISE"))
        orchestrator = ContinuousIntelligenceOrchestrator(telemetry=telemetry)
        cycle = orchestrator.cycle()
        self.assertGreaterEqual(len(cycle.signals), 1)
        self.assertEqual(len(cycle.ingested), len(cycle.signals))
        self.assertEqual(len(orchestrator.decision_queue.pending()), len(cycle.signals))
        self.assertTrue(all(item.status == "PENDING" for item in orchestrator.decision_queue.pending()))

    def test_owner_is_required(self):
        with self.assertRaises(ValueError):
            ContinuousIntelligenceOrchestrator(owner="")


if __name__ == "__main__":
    unittest.main()
