import unittest
from types import SimpleNamespace
from src.federated_telemetry import FederatedTelemetryEngine

class FederatedTelemetryTests(unittest.TestCase):
    def item(self, account, instance, qa=True, evidence=1, drift=False):
        identity = SimpleNamespace(account_id=account, instance_id=instance)
        telemetry = SimpleNamespace(qa_passed=qa, blocked=False, evidence_count=evidence, drift_detected=drift, revalidation_triggered=False)
        return SimpleNamespace(identity=identity, telemetry=telemetry)

    def test_aggregates_accounts_instances_and_health(self):
        records = [self.item("a", "i1"), self.item("b", "i2", drift=True), self.item("a", "i3", qa=False, evidence=0)]
        snapshot = FederatedTelemetryEngine().snapshot(records)
        self.assertEqual(snapshot.executions, 3)
        self.assertEqual(snapshot.accounts, 2)
        self.assertEqual(snapshot.instances, 3)
        self.assertAlmostEqual(snapshot.qa_pass_rate, 2 / 3)
        self.assertAlmostEqual(snapshot.evidence_coverage, 2 / 3)
        self.assertAlmostEqual(snapshot.drift_rate, 1 / 3)

    def test_empty_snapshot(self):
        snapshot = FederatedTelemetryEngine().snapshot([])
        self.assertEqual(snapshot.executions, 0)

if __name__ == "__main__":
    unittest.main()
