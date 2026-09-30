import unittest
from src.evidence_collector import EvidenceCollector
class EvidenceCollectorTests(unittest.TestCase):
    def test_collects_complete_explicit_evidence(self):
        c=EvidenceCollector(); p=c.collect({"health":"passed","telemetry":"active"},required=("health","telemetry"))
        self.assertTrue(p.complete); c.require_complete(p)
    def test_missing_evidence_blocks_completion(self):
        c=EvidenceCollector(); p=c.collect({"health":"passed"},required=("health","telemetry"))
        self.assertFalse(p.complete)
        with self.assertRaises(RuntimeError): c.require_complete(p)
    def test_invalid_inputs_rejected(self):
        c=EvidenceCollector()
        with self.assertRaises(ValueError): c.collect({},required=())
        with self.assertRaises(ValueError): c.collect({"health":True},required=("health",))
if __name__ == "__main__": unittest.main()
