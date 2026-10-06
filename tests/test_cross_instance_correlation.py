import unittest
from src.cross_instance_correlation import CrossInstanceAnomalyCorrelator, InstanceAnomaly

class CrossInstanceCorrelationTests(unittest.TestCase):
    def test_same_metric_across_instances_becomes_systemic(self):
        items=(InstanceAnomaly('a','drift_rate','HIGH',0.2),InstanceAnomaly('b','drift_rate','HIGH',0.3))
        result=CrossInstanceAnomalyCorrelator().correlate(items)
        self.assertEqual(result[0].instance_count,2)
        self.assertTrue(result[0].systemic)
        self.assertAlmostEqual(result[0].mean_delta,0.25)

    def test_single_instance_is_not_systemic(self):
        items=(InstanceAnomaly('a','qa_pass_rate','HIGH',-0.2),)
        result=CrossInstanceAnomalyCorrelator().correlate(items)
        self.assertFalse(result[0].systemic)

if __name__=='__main__': unittest.main()
