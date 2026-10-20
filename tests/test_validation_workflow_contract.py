import os
import re
import unittest
from pathlib import Path


WORKFLOW_PATH = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "validation.yml"


class ValidationWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    def test_deployment_bundle_runs_after_all_prerequisites_even_on_failure(self):
        self.assertRegex(
            self.workflow,
            r"deployment-evidence-bundle:\s*\n\s*if:\s*\$\{\{\s*always\(\)\s*\}\}\s*\n\s*needs:\s*\[tests, performance-evidence, repository-validation\]",
        )

    def test_upload_precedes_final_prerequisite_guard(self):
        upload = self.workflow.index("name: kmh-oia-deployment-evidence-bundle")
        guard = self.workflow.index("name: Enforce prerequisite jobs succeeded")
        self.assertLess(upload, guard)
        self.assertIn("if: ${{ always() }}", self.workflow[guard:])

    def test_guard_checks_every_required_prerequisite_result(self):
        guard = self.workflow.index("name: Enforce prerequisite jobs succeeded")
        guard_text = self.workflow[guard:]
        for expression in (
            "TESTS_RESULT: ${{ needs.tests.result }}",
            "PERFORMANCE_RESULT: ${{ needs.performance-evidence.result }}",
            "REPOSITORY_RESULT: ${{ needs.repository-validation.result }}",
        ):
            self.assertIn(expression, guard_text)
        self.assertIn('result != "success"', guard_text)
        self.assertIn("raise SystemExit(1)", guard_text)

    def test_receipt_generator_does_not_use_quoted_json_heredoc(self):
        self.assertNotIn("<<'JSON'", self.workflow)
        self.assertIn('json.dumps(rows, indent=2)', self.workflow)

    def test_bundle_validator_requires_success_for_each_required_receipt(self):
        self.assertIn('row.get("conclusion") != "success"', self.workflow)
        self.assertIn("Verified three required CI receipts", self.workflow)


if __name__ == "__main__":
    unittest.main()
