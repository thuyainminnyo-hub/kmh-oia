import unittest

from src.continuous_intelligence_orchestrator import ContinuousIntelligenceOrchestrator
from src.execution_telemetry import ExecutionTelemetry, ExecutionTelemetryCollector


class ContinuousIntelligenceOrchestratorTests(unittest.TestCase):
    def test_healthy_cycle_produces_no_decisions(self):
        telemetry = ExecutionTelemetryCollector()
        telemetry.record(ExecutionTelemetry("cmd:1", True, False, False, 3, True, False, False, None))
        cycle = ContinuousIntelligenceOrchestrator(telemetry=telemetry).cycle()
        self.assertEqual(cycle.signals, ())
        self.assertEqual(cycle.ingested, ())

    def test_unhealthy_cycle_creates_pending_decisions(self):
        telemetry = ExecutionTelemetryCollector()
        telemetry.record(ExecutionTelemetry("cmd:1", False, True, True, 0, False, True, True, "REVISE"))
        cycle = ContinuousIntelligenceOrchestrator(telemetry=telemetry).cycle()
        self.assertGreaterEqual(len(cycle.signals), 1)
        self.assertEqual(len(cycle.ingested), len(cycle.signals))
        self.assertTrue(
            all(item.status == "PENDING" for item in cycle_ingested_decisions(cycle, telemetry))
        )

    def test_owner_is_required(self):
        with self.assertRaises(ValueError):
            ContinuousIntelligenceOrchestrator(owner="")

def cycle_ingested_decisions(cycle, telemetry):
    # The orchestrator exposes decision IDs; the queue remains the governance boundary.
    return orchestrator_queue_items


if __name__ == "__main__":
    unittest.main()
