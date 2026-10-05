import unittest
from src.standard_control_plane import StandardControlPlane
from src.standardization_engine import OperatingStandard

class StandardControlPlaneTests(unittest.TestCase):
    def setUp(self):
        self.standard = OperatingStandard("std:a:v1","a","Require evidence","Higher quality",1,"ACTIVE")
        self.plane = StandardControlPlane()
        self.plane.register(self.standard)

    def test_no_drift_has_no_trigger(self):
        result = self.plane.observe(self.standard,"cmd:1",applied_rule="Require evidence",evidence_id="ev:1")
        self.assertTrue(result.compliance.compliant)
        self.assertFalse(result.drift.drifted)
        self.assertIsNone(result.trigger)

    def test_drift_creates_trigger_and_revalidates(self):
        result = self.plane.observe(self.standard,"cmd:2",applied_rule="Skip evidence",evidence_id="ev:2")
        self.assertFalse(result.compliance.compliant)
        self.assertTrue(result.drift.drifted)
        self.assertIsNotNone(result.trigger)
        completed = self.plane.revalidate(result,self.standard,observed_effect=0.2,outcome_positive=True)
        self.assertEqual(completed.revalidation.revalidation.verdict,"VALID")
        self.assertEqual(completed.revalidation.lifecycle.action,"KEEP")

    def test_revalidation_without_drift_rejected(self):
        result = self.plane.observe(self.standard,"cmd:3",applied_rule="Require evidence",evidence_id="ev:3")
        with self.assertRaises(ValueError):
            self.plane.revalidate(result,self.standard,observed_effect=0,outcome_positive=False)

if __name__ == "__main__": unittest.main()
