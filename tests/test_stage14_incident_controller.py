import unittest
from src.incident_controller import IncidentController
class IncidentControllerTests(unittest.TestCase):
    def test_lifecycle_requires_evidence_and_validation(self):
        c=IncidentController(); s=c.open(incident_id="INC-1",severity="high",reason="health failure")
        s=c.capture_evidence(s); self.assertTrue(s.evidence_captured)
        s=c.resolve(s,validated=True); self.assertEqual(s.phase,"resolved")
    def test_invalid_inputs_rejected(self):
        c=IncidentController()
        with self.assertRaises(ValueError): c.open(incident_id="",severity="high",reason="x")
        with self.assertRaises(ValueError): c.open(incident_id="1",severity="unknown",reason="x")
        with self.assertRaises(ValueError): c.open(incident_id="1",severity="high",reason="")
    def test_resolution_cannot_skip_evidence_or_validation(self):
        c=IncidentController(); s=c.open(incident_id="1",severity="critical",reason="x")
        with self.assertRaises(RuntimeError): c.resolve(s,validated=True)
        s=c.capture_evidence(s)
        with self.assertRaises(RuntimeError): c.resolve(s,validated=False)
if __name__ == "__main__": unittest.main()
