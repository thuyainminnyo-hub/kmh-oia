import unittest
from src.adaptation_validation import AdaptationValidationEngine
from src.standardization_engine import StandardizationEngine
from src.standard_runtime_bridge import StandardRuntimeBridge

class StandardRuntimeBridgeTests(unittest.TestCase):
    def setUp(self):
        e=AdaptationValidationEngine().evaluate("adapt:runtime",80,90)
        s=StandardizationEngine()
        self.standard=s.activate(s.approve(s.propose(e,rule="Require evidence before QA",expected_effect="Higher QA pass rate")))
        self.bridge=StandardRuntimeBridge()

    def test_compliant_active_standard_allows_runtime(self):
        check=self.bridge.authorize(self.standard,"cmd:runtime",applied_rule="Require evidence before QA")
        self.assertTrue(check.allowed)
        self.assertTrue(check.compliance.compliant)

    def test_non_compliant_rule_blocks_runtime(self):
        with self.assertRaises(PermissionError):
            self.bridge.authorize(self.standard,"cmd:runtime",applied_rule="Skip QA")

    def test_retired_standard_cannot_authorize(self):
        retired=StandardizationEngine().retire(self.standard)
        with self.assertRaises(ValueError):
            self.bridge.authorize(retired,"cmd:runtime",applied_rule=retired.rule)

if __name__ == "__main__": unittest.main()
