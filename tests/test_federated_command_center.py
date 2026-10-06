import unittest
from types import SimpleNamespace
from src.command_center_cycle_adapter import CommandCenterView
from src.federated_command_center import FederatedCommandCenterAdapter
from src.federated_telemetry import FederatedHealthSnapshot

class FederatedCommandCenterTests(unittest.TestCase):
    def test_drift_becomes_actionable_signal(self):
        view = CommandCenterView("Goal", object(), 0, 0, (), (), 0, 0)
        health = FederatedHealthSnapshot(3, 2, 2, 1.0, 0.0, 1.0, 1/3, 0.0)
        result = FederatedCommandCenterAdapter().build(view, health)
        self.assertEqual(result.command_center.signals, 1)
        self.assertEqual(result.command_center.blockers, ())

    def test_blocked_federated_runtime_surfaces_blocker(self):
        view = CommandCenterView("Goal", object(), 0, 0, (), (), 0, 0)
        health = FederatedHealthSnapshot(3, 2, 2, 2/3, 1/3, 1.0, 0.0, 0.0)
        result = FederatedCommandCenterAdapter().build(view, health)
        self.assertEqual(len(result.command_center.blockers), 1)

if __name__ == "__main__":
    unittest.main()
