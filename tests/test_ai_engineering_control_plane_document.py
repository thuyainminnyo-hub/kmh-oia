"""Structural contract checks for the AI Engineering Control Plane baseline.

These tests verify that the architecture contract retains its mandatory controls.
They do not claim runtime model routing or provider integration exists.
"""
from pathlib import Path
import unittest


DOC = Path(__file__).resolve().parents[1] / "docs" / "architecture" / "ai-engineering-control-plane-v1.md"


class AIEngineeringControlPlaneDocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = DOC.read_text(encoding="utf-8")

    def test_existing_runtime_path_is_preserved(self):
        self.assertIn("Input Gateway", self.content)
        self.assertIn("Tool Security", self.content)
        self.assertIn("Governed Tool", self.content)
        self.assertIn("Trace", self.content)

    def test_fail_closed_and_no_self_certification_are_explicit(self):
        self.assertIn("Deny by default", self.content)
        self.assertIn("No self-certification", self.content)
        self.assertIn("No direct model-to-core mutation", self.content)

    def test_runtime_cost_controls_are_explicit(self):
        self.assertIn("per-request and per-session budget", self.content)
        self.assertIn("Paid inference is disabled", self.content)
        self.assertIn("maximum input/output tokens", self.content)

    def test_learning_and_production_are_separate_gates(self):
        self.assertIn("learning NOT_ADMITTED", self.content)
        self.assertIn("G5 — Learning", self.content)
        self.assertIn("G6 — Production", self.content)

    def test_document_does_not_claim_runtime_provider_integration(self):
        self.assertIn("No model provider is selected or called", self.content)
        self.assertIn("Not started", self.content)


if __name__ == "__main__":
    unittest.main()
