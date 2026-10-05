import unittest
from src.standard_registry import StandardVersionRegistry
from src.standardization_engine import OperatingStandard
from src.drift_revalidation import DriftRevalidationTrigger

class DriftRevalidationTests(unittest.TestCase):
    def test_drift_creates_trigger(self):
        standard=OperatingStandard("std:a:v1","a","Require evidence","Higher quality",1,"ACTIVE")
        drift=StandardVersionRegistry().detect_drift(standard,"cmd:1","Skip evidence")
        trigger=DriftRevalidationTrigger().create(drift,evidence_id="ev:1")
        self.assertEqual(trigger.status,"TRIGGERED")
        self.assertEqual(trigger.standard_id,"std:a:v1")

    def test_no_drift_cannot_trigger(self):
        standard=OperatingStandard("std:a:v1","a","Require evidence","Higher quality",1,"ACTIVE")
        drift=StandardVersionRegistry().detect_drift(standard,"cmd:1","Require evidence")
        with self.assertRaises(ValueError):
            DriftRevalidationTrigger().create(drift,evidence_id="ev:1")

    def test_trigger_resolves(self):
        standard=OperatingStandard("std:a:v1","a","Require evidence","Higher quality",1,"ACTIVE")
        drift=StandardVersionRegistry().detect_drift(standard,"cmd:1","Skip evidence")
        engine=DriftRevalidationTrigger()
        trigger=engine.create(drift,evidence_id="ev:1")
        self.assertEqual(engine.resolve(trigger).status,"RESOLVED")

if __name__ == "__main__": unittest.main()
