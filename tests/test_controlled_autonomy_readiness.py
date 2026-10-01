"""Tests for controlled autonomy readiness evidence gate."""
import unittest

from src.controlled_autonomy_readiness import ControlledAutonomyReadinessGate


class ControlledAutonomyReadinessGateTests(unittest.TestCase):
    def setUp(self):
        self.gate = ControlledAutonomyReadinessGate()
        self.evidence = {key: "verified artifact reference" for key in self.gate.REQUIRED_EVIDENCE}

    def test_complete_evidence_is_ready_for_review_not_authorized(self):
        result = self.gate.assess(scope="read-only bounded assistance", evidence=self.evidence)
        self.assertEqual(result.phase, "evidence_ready_for_review")
        self.assertFalse(result.production_authorized)
        self.gate.require_ready(result)

    def test_missing_evidence_blocks(self):
        evidence = dict(self.evidence)
        del evidence["human_oversight"]
        result = self.gate.assess(scope="bounded", evidence=evidence)
        self.assertIn("human_oversight", result.missing)
        with self.assertRaises(RuntimeError):
            self.gate.require_ready(result)

    def test_empty_evidence_value_is_missing(self):
        evidence = dict(self.evidence, rollback_plan=" ")
        result = self.gate.assess(scope="bounded", evidence=evidence)
        self.assertIn("rollback_plan", result.missing)

    def test_invalid_inputs_rejected(self):
        with self.assertRaises(ValueError):
            self.gate.assess(scope="", evidence=self.evidence)
        with self.assertRaises(ValueError):
            self.gate.assess(scope="bounded", evidence=None)
        with self.assertRaises(ValueError):
            self.gate.assess(scope="bounded", evidence={"bounded_scope": 4})

    def test_scope_is_required_and_production_authority_stays_false(self):
        result = self.gate.assess(scope="bounded", evidence=self.evidence)
        self.assertFalse(result.production_authorized)
        with self.assertRaises(RuntimeError):
            self.gate.require_ready(None)


if __name__ == "__main__":
    unittest.main()
