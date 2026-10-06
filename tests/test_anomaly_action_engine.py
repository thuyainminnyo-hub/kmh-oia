import unittest
from src.anomaly_action_engine import AnomalyActionEngine
from src.federated_anomaly import FederatedAnomaly

class AnomalyActionEngineTests(unittest.TestCase):
    def test_maps_drift_to_specific_action(self):
        anomaly = FederatedAnomaly("drift_rate", 0.0, 0.2, 0.2, 0.1, "HIGH", True)
        result = AnomalyActionEngine().recommend(anomaly)
        self.assertEqual(result.next_action.priority, 1)
        self.assertIn("standard drift", result.next_action.action)

    def test_maps_quality_to_specific_action(self):
        anomaly = FederatedAnomaly("qa_pass_rate", 1.0, 0.8, -0.2, 0.1, "HIGH", True)
        result = AnomalyActionEngine().recommend(anomaly)
        self.assertIn("QA degradation", result.next_action.action)

    def test_undetected_anomaly_has_no_action(self):
        anomaly = FederatedAnomaly("drift_rate", 0.0, 0.0, 0.0, 0.1, "NONE", False)
        result = AnomalyActionEngine().recommend(anomaly)
        self.assertEqual(result.next_action.kind, "NONE")

if __name__ == "__main__":
    unittest.main()
