"""Tests for Stage 14 Stage 15 handoff controller."""
import unittest

from src.operational_evidence_package import (
    OperationalEvidencePackageBuilder,
)
from src.stage15_handoff import Stage15HandoffController


class Stage15HandoffTests(unittest.TestCase):
    def setUp(self):
        self.builder = OperationalEvidencePackageBuilder()
        self.controller = Stage15HandoffController()
        self.evidence = {key: "verified-reference" for key in self.builder.REQUIRED_EVIDENCE}
        self.package = self.builder.build(deployment_id="deployment-1", evidence=self.evidence)

    def test_complete_evidence_and_acknowledgement_enable_handoff(self):
        state = self.controller.prepare(
            self.package, production_boundary_acknowledged=True
        )
        self.assertEqual(state.phase, "ready")
        self.assertTrue(state.ready)
        self.controller.validate(state)

    def test_incomplete_evidence_blocks_handoff(self):
        package = self.builder.build(deployment_id="deployment-1", evidence={})
        state = self.controller.prepare(package, production_boundary_acknowledged=True)
        self.assertEqual(state.phase, "blocked")
        self.assertFalse(state.ready)
        with self.assertRaises(RuntimeError):
            self.controller.validate(state)

    def test_missing_boundary_acknowledgement_blocks_handoff(self):
        state = self.controller.prepare(
            self.package, production_boundary_acknowledged=False
        )
        self.assertEqual(state.phase, "blocked")
        self.assertTrue(state.evidence_complete)
        self.assertFalse(state.production_boundary_acknowledged)

    def test_invalid_package_and_acknowledgement_rejected(self):
        with self.assertRaises(ValueError):
            self.controller.prepare(None, production_boundary_acknowledged=True)
        with self.assertRaises(ValueError):
            self.controller.prepare(self.package, production_boundary_acknowledged="yes")


if __name__ == "__main__":
    unittest.main()
