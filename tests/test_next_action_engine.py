import unittest

from src.command_center_cycle_adapter import CommandCenterCycleAdapter
from src.continuous_intelligence_orchestrator import ContinuousIntelligenceOrchestrator
from src.execution_telemetry import ExecutionTelemetry, ExecutionTelemetryCollector
from src.live_operating_console import LiveOperatingConsole
from src.next_action_engine import NextActionEngine
from src.operating_cycle_monitor import OperatingCycleMonitor


class NextActionEngineTests(unittest.TestCase):
    def view(self, *, blocker=False, qa=False, evidence=False, decisions=0, signals=0, objective=""):
        console = LiveOperatingConsole(date="2026-10-05", primary_objective=objective)
        if blocker:
            command = console.add_command(objective="blocked work", priority="P1", owner="system", expected_output="done")
            console.transition(command.id, "QUALIFIED")
            console.transition(command.id, "READY")
            console.transition(command.id, "ACTIVE")
            console.transition(command.id, "BLOCKED")
        if qa:
            command = console.add_command(objective="qa work", priority="P1", owner="system", expected_output="done")
            console.transition(command.id, "QUALIFIED")
            console.transition(command.id, "READY")
            console.transition(command.id, "ACTIVE")
            console.transition(command.id, "COMPLETED")
            console.attach_evidence(command.id, "trace")
        if evidence:
            command = console.add_command(objective="evidence work", priority="P1", owner="system", expected_output="done")
            console.transition(command.id, "QUALIFIED")
            console.transition(command.id, "READY")
            console.transition(command.id, "ACTIVE")
            console.transition(command.id, "COMPLETED")
        telemetry = ExecutionTelemetryCollector()
        if signals:
            telemetry.record(ExecutionTelemetry("cmd:1", False, True, True, 0, False, True, True, "REVISE"))
        else:
            telemetry.record(ExecutionTelemetry("cmd:1", True, False, False, 2, True, False, False, None))
        cycle = ContinuousIntelligenceOrchestrator(telemetry=telemetry).cycle()
        monitored = OperatingCycleMonitor().snapshot(cycle)
        return CommandCenterCycleAdapter().build(monitored, console)

    def test_blocker_has_highest_priority(self):
        action = NextActionEngine().recommend(self.view(blocker=True, signals=1))
        self.assertEqual(action.kind, "BLOCKER")

    def test_qa_beats_evidence_and_decisions(self):
        action = NextActionEngine().recommend(self.view(qa=True, evidence=True, decisions=1))
        self.assertEqual(action.kind, "QA")

    def test_pending_decision_beats_signal(self):
        action = NextActionEngine().recommend(self.view(decisions=1, signals=1))
        self.assertEqual(action.kind, "DECISION")

    def test_objective_is_fallback(self):
        action = NextActionEngine().recommend(self.view(objective="Ship the highest-leverage improvement."))
        self.assertEqual(action.kind, "OBJECTIVE")

    def test_no_work_returns_none(self):
        action = NextActionEngine().recommend(self.view())
        self.assertEqual(action.kind, "NONE")


if __name__ == "__main__":
    unittest.main()
