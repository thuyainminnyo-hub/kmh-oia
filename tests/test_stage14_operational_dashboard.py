import unittest
from src.operational_dashboard import OperationalDashboard
class OperationalDashboardTests(unittest.TestCase):
    def test_snapshot_is_deterministic(self):
        s=OperationalDashboard().snapshot(status="stable",metrics={"errors":"0","latency":"12ms"})
        self.assertEqual(s.metrics,(("errors","0"),("latency","12ms")))
    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError): OperationalDashboard().snapshot(status="",metrics={})
    def test_invalid_metric_rejected(self):
        with self.assertRaises(ValueError): OperationalDashboard().snapshot(status="ok",metrics={"":"x"})
if __name__ == "__main__": unittest.main()
