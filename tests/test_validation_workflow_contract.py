import unittest
from pathlib import Path


WORKFLOW_PATH = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "validation.yml"
PREREQUISITE_CHECK_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_prerequisite_results.py"


class ValidationWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        cls.prerequisite_check = PREREQUISITE_CHECK_PATH.read_text(encoding="utf-8")

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

    def test_guard_passes_every_required_prerequisite_result_to_helper(self):
        guard = self.workflow.index("name: Enforce prerequisite jobs succeeded")
        guard_text = self.workflow[guard:]
        for expression in (
            "TESTS_RESULT: ${{ needs.tests.result }}",
            "PERFORMANCE_RESULT: ${{ needs.performance-evidence.result }}",
            "REPOSITORY_RESULT: ${{ needs.repository-validation.result }}",
        ):
            self.assertIn(expression, guard_text)
        self.assertIn("python scripts/check_prerequisite_results.py", guard_text)

    def test_helper_fails_closed_for_any_non_success_result(self):
        self.assertIn('result != "success"', self.prerequisite_check)
        self.assertIn("return 1", self.prerequisite_check)
        self.assertIn("All required prerequisite jobs succeeded.", self.prerequisite_check)

    def test_receipt_generator_does_not_use_quoted_json_heredoc(self):
        self.assertNotIn("<<'JSON'", self.workflow)
        self.assertIn("json.dumps(rows, indent=2)", self.workflow)

    def test_bundle_validator_requires_success_for_each_required_receipt(self):
        self.assertIn('row.get("conclusion") != "success"', self.workflow)
        self.assertIn("Verified three required CI receipts", self.workflow)


if __name__ == "__main__":
    unittest.main()
