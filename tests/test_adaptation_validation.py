import unittest
from src.adaptation_validation import AdaptationValidationEngine

class AdaptationValidationTests(unittest.TestCase):
    def test_improvement(self):
        e=AdaptationValidationEngine().evaluate("adapt:1",10,15)
        self.assertEqual(e.verdict,"IMPROVED"); self.assertTrue(e.relative_change>0); self.assertTrue(AdaptationValidationEngine().should_standardize(e))
    def test_regression_when_lower_is_better(self):
        e=AdaptationValidationEngine().evaluate("adapt:1",10,7,higher_is_better=False)
        self.assertEqual(e.verdict,"IMPROVED")
    def test_no_improvement(self):
        e=AdaptationValidationEngine().evaluate("adapt:1",10,10)
        self.assertEqual(e.verdict,"NO_IMPROVEMENT"); self.assertTrue(AdaptationValidationEngine().should_revise(e))
    def test_rejects_negative_metric(self):
        with self.assertRaises(ValueError): AdaptationValidationEngine().evaluate("adapt:1",-1,2)
if __name__=="__main__": unittest.main()
