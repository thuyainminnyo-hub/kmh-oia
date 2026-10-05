import unittest

from src.continuous_intelligence_orchestrator import ContinuousIntelligenceOrchestrator
from src.execution_telemetry import ExecutionTelemetry, ExecutionTelemetryCollector
from src.operating_cycle_monitor import OperatingCycleMonitor


class OperatingCycleMonitorTests(unittest.TestCase):
    def test_healthy_cycle_has_zero_signals_and_decisions(self):
        telemetry = ExecutionTelemetryCollector()
        telemetry.record(ExecutionTelemetry("cmd:1", True, False, False, 2, None, False, False, None))
        cycle = ContinuousIntelligenceOrchestrator(telemetry=telemetry).cycle()
        snapshot = OperatingCycleMonitor().snapshot(cycle)

        self.assertEqual(snapshot.health.executions, 1)
        self.assertEqual(snapshot.signal_count, 0)
        self.assertEqual(snapshot.pending_decision_count, 0)
        self.assertEqual(snapshot.decision_ids, ())

    def test_unhealthy_cycle_exposes_decision_backlog(self):
        telemetry = ExecutionTelemetryCollector()
        telemetry.record(ExecutionTelemetry("cmd:1", False, True, True, 0, False, True, True, "REVISE"))
        orchestrator = ContinuousIntelligenceOrchestrator(telemetry=telemetry)
        cycle = orchestrator.cycle()
        snapshot = OperatingCycleMonitor().snapshot(cycle)

        self.assertGreater(snapshot.signal_count, 0)
        self.assertEqual(snapshot.pending_decision_count, snapshot.signal_count)
        self.assertEqual(len(snapshot.decision_ids), snapshot.pending_decision_count)

if __name__ == "__main__":
    unittest.main()
