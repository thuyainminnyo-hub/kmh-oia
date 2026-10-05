import unittest
from src.adaptation_validation import AdaptationValidationEngine
from src.standardization_engine import StandardizationEngine
from src.standard_runtime_bridge import StandardRuntimeBridge
from src.standard_compliance_evidence import StandardComplianceEvidenceBuilder

class StandardComplianceEvidenceTests(unittest.TestCase):
    def setUp(self):
        experiment=AdaptationValidationEngine().evaluate("adapt:evidence",80,90)
        engine=StandardizationEngine()
        standard=engine.activate(engine.approve(engine.propose(experiment,rule="Require evidence before QA",expected_effect="Higher QA pass rate")))
        self.check=StandardRuntimeBridge().authorize(standard,"cmd:evidence",applied_rule=standard.rule)

    def test_compliant_check_becomes_qa_evidence(self):
        evidence=StandardComplianceEvidenceBuilder().build(self.check,rule=self.check.compliance.reason.split(";")[0])
        self.assertEqual(evidence.command_id,"cmd:evidence")
        self.assertEqual(evidence.evidence_type,"standard_compliance")
        self.assertEqual(evidence.qa_status,"PASS")

    def test_invalid_qa_status_rejected(self):
        with self.assertRaises(ValueError):
            StandardComplianceEvidenceBuilder().build(self.check,rule="Require evidence before QA",qa_status="PENDING")

if __name__ == "__main__": unittest.main()
