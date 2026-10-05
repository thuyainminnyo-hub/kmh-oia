import unittest
from src.adaptation_validation import AdaptationValidationEngine
from src.standardization_engine import StandardizationEngine
from src.standard_enforcement import StandardEnforcementEngine

class StandardEnforcementTests(unittest.TestCase):
    def setUp(self):
        e=AdaptationValidationEngine().evaluate("adapt:1",80,90)
        s=StandardizationEngine().activate(StandardizationEngine().approve(StandardizationEngine().propose(e,rule="Require evidence before QA",expected_effect="Higher QA pass rate")))
        self.standard=s; self.engine=StandardEnforcementEngine()
    def test_active_standard_requires_compliance_and_evidence(self):
        c=self.engine.check(self.standard,"cmd:1",applied_rule="Require evidence before QA",evidence_attached=True)
        self.assertTrue(c.compliant)
    def test_missing_evidence_is_not_compliant(self):
        c=self.engine.check(self.standard,"cmd:1",applied_rule="Require evidence before QA",evidence_attached=False)
        self.assertFalse(c.compliant)
    def test_wrong_rule_is_not_compliant(self):
        c=self.engine.check(self.standard,"cmd:1",applied_rule="Skip QA",evidence_attached=True)
        self.assertFalse(c.compliant)
    def test_retired_standard_cannot_be_enforced(self):
        retired=StandardEnforcementTests._retire(self.standard)
        with self.assertRaises(ValueError): self.engine.check(retired,"cmd:1",applied_rule=retired.rule,evidence_attached=True)
    @staticmethod
    def _retire(s):
        return StandardizationEngine().retire(s)
if __name__ == "__main__": unittest.main()
