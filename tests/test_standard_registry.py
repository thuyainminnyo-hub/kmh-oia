import unittest
from src.standard_registry import StandardVersionRegistry
from src.standardization_engine import OperatingStandard

class StandardRegistryTests(unittest.TestCase):
    def test_register_and_find_active(self):
        registry=StandardVersionRegistry()
        standard=OperatingStandard("std:a:v1","a","Require evidence","Higher quality",1,"ACTIVE")
        registry.register(standard)
        self.assertEqual(registry.active("a"),standard)
        self.assertEqual(len(registry.versions("a")),1)

    def test_drift_detected(self):
        registry=StandardVersionRegistry()
        standard=OperatingStandard("std:a:v1","a","Require evidence","Higher quality",1,"ACTIVE")
        result=registry.detect_drift(standard,"cmd:1","Skip evidence")
        self.assertTrue(result.drifted)

    def test_no_drift(self):
        registry=StandardVersionRegistry()
        standard=OperatingStandard("std:a:v1","a","Require evidence","Higher quality",1,"ACTIVE")
        result=registry.detect_drift(standard,"cmd:1","Require evidence")
        self.assertFalse(result.drifted)

if __name__ == "__main__": unittest.main()
