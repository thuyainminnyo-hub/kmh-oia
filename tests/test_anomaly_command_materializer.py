import unittest
from src.anomaly_action_engine import AnomalyActionEngine
from src.anomaly_command_materializer import AnomalyCommandMaterializer
from src.federated_anomaly import FederatedAnomaly
from src.live_operating_console import LiveOperatingConsole

class AnomalyCommandMaterializerTests(unittest.TestCase):
    def test_materializes_high_anomaly_as_p1_inbox_command(self):
        anomaly = FederatedAnomaly("drift_rate", 0.0, 0.2, 0.2, 0.1, "HIGH", True)
        action = AnomalyActionEngine().recommend(anomaly)
        result = AnomalyCommandMaterializer().materialize(action, LiveOperatingConsole(date="2026-10-04"), owner="ops", expected_output="drift reviewed")
        self.assertEqual(result.command.priority, "P1")
        self.assertEqual(result.command.status, "INBOX")
        self.assertEqual(result.command.source_action_kind, "SIGNAL")

    def test_undetected_anomaly_is_not_materialized(self):
        anomaly = FederatedAnomaly("drift_rate", 0.0, 0.0, 0.0, 0.1, "NONE", False)
        action = AnomalyActionEngine().recommend(anomaly)
        with self.assertRaises(ValueError):
            AnomalyCommandMaterializer().materialize(action, LiveOperatingConsole(date="2026-10-04"), owner="ops", expected_output="none")

if __name__ == "__main__": unittest.main()
