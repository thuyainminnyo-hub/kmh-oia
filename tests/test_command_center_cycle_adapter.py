import unittest

from src.command_center_cycle_adapter import CommandCenterCycleAdapter
from src.continuous_intelligence_orchestrator import ContinuousIntelligenceOrchestrator
from src.execution_telemetry import ExecutionTelemetry, ExecutionTelemetryCollector
from src.live_operating_console import LiveOperatingConsole
from src.operating_cycle_monitor import OperatingCycleMonitor


class CommandCenterCycleAdapterTests(unittest.TestCase):
    def test_cycle_maps_into_operational_command_center_view(self):
        telemetry = ExecutionTelemetryCollector()
        telemetry.record(
            ExecutionTelemetry("cmd:1", False, True, True, 0, False, True, True, "REVISE")
        )
        cycle = ContinuousIntelligenceOrchestrator(telemetry=telemetry).cycle()
        monitored = OperatingCycleMonitor().snapshot(cycle)
        console = LiveOperatingConsole(
            date="2026-10-05",
            primary_objective="Stabilize execution quality",
        )
        view = CommandCenterCycleAdapter().build(monitored, console)

        self.assertEqual(view.primary_objective, "Stabilize execution quality")
        self.assertGreater(view.signals, 0)
        self.assertEqual(view.pending_decisions, view.signals)
        self.assertEqual(len(view.decision_ids), view.pending_decisions)
        self.assertEqual(view.blockers, ())
        self.assertEqual(view.evidence_pending, 0)

    def test_adapter_does_not_mutate_console(self):
        console = LiveOperatingConsole(date="2026-10-05", primary_objective="Today")
        before = console.snapshot()
        telemetry = ExecutionTelemetryCollector()
        telemetry.record(ExecutionTelemetry("cmd:1", True, False, False, 2, True, False, False, None))
        cycle = ContinuousIntelligenceOrchestrator(telemetry=telemetry).cycle()
        monitored = OperatingCycleMonitor().snapshot(cycle)
        CommandCenterCycleAdapter().build(monitored, console)
        self.assertEqual(console.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
