import unittest
from src.operational_baseline import OperationalBaselineBuilder
class OperationalBaselineBuilderTests(unittest.TestCase):
    def test_builds_bounded_baseline(self):
        b=OperationalBaselineBuilder().build([{"health":True},{"health":True},{"health":False}])
        self.assertEqual(b.samples,3); self.assertEqual(b.healthy_samples,2); self.assertAlmostEqual(b.success_rate,2/3); self.assertFalse(b.stable)
    def test_all_healthy_samples_are_stable(self):
        b=OperationalBaselineBuilder().build([{"health":True},{"health":True}])
        self.assertTrue(b.stable); self.assertEqual(b.success_rate,1.0)
    def test_empty_samples_rejected(self):
        with self.assertRaisesRegex(ValueError,"samples"):
            OperationalBaselineBuilder().build([])
if __name__ == "__main__": unittest.main()
