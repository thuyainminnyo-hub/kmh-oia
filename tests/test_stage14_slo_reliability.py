import unittest
from src.slo_reliability import SloReliabilityController
class SloReliabilityControllerTests(unittest.TestCase):
    def test_reports_observed_reliability(self):
        r=SloReliabilityController().evaluate([True,True,False,True])
        self.assertEqual(r.samples,4); self.assertEqual(r.healthy_samples,3); self.assertAlmostEqual(r.observed_success_rate,.75); self.assertFalse(r.reliable)
    def test_all_healthy_samples_are_reliable(self):
        self.assertTrue(SloReliabilityController().evaluate([True,True]).reliable)
    def test_empty_and_non_boolean_samples_rejected(self):
        c=SloReliabilityController()
        with self.assertRaises(ValueError): c.evaluate([])
        with self.assertRaises(ValueError): c.evaluate([True,1])
if __name__ == "__main__": unittest.main()
