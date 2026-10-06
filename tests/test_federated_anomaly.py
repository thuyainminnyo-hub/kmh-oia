import unittest
from src.federated_anomaly import FederatedAnomalyDetector, FederatedBaseline
from src.federated_telemetry import FederatedHealthSnapshot

class FederatedAnomalyTests(unittest.TestCase):
    def health(self, qa=1.0, blocked=0.0, evidence=1.0, drift=0.0, reval=0.0):
        return FederatedHealthSnapshot(10, 2, 2, qa, blocked, evidence, drift, reval)

    def test_detects_quality_and_drift_anomalies(self):
        baseline = FederatedBaseline(1.0, 0.0, 1.0, 0.0, 0.0)
        result = FederatedAnomalyDetector().detect(baseline, self.health(qa=.8, drift=.2))
        self.assertTrue(result[0].detected)
        self.assertTrue(result[3].detected)

    def test_stable_health_has_no_anomaly(self):
        baseline = FederatedBaseline(1.0, 0.0, 1.0, 0.0, 0.0)
        result = FederatedAnomalyDetector().detect(baseline, self.health())
        self.assertFalse(any(x.detected for x in result))

    def test_negative_threshold_rejected(self):
        with self.assertRaises(ValueError):
            FederatedAnomalyDetector().detect(FederatedBaseline(1,0,1,0,0), self.health(), -0.1)

if __name__ == "__main__":
    unittest.main()
