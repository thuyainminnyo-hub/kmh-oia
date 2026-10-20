import json
import tempfile
import unittest
from pathlib import Path

from scripts.capture_ci_evidence import capture_ci_evidence


GOOD = {
    "url": "https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/12345",
    "head_sha": "a" * 40,
    "bundle_sha": "a" * 40,
    "tests": "success",
    "performance": "success",
    "repository": "success",
}


class CaptureCIEvidenceTests(unittest.TestCase):
    def test_green_prerequisites_are_captured_without_errors(self):
        rows, diagnostics = capture_ci_evidence(GOOD)
        self.assertEqual(len(rows), 3)
        self.assertEqual([row["conclusion"] for row in rows], ["success"] * 3)
        self.assertEqual(diagnostics["capture_status"], "CAPTURED")
        self.assertEqual(diagnostics["validation_errors"], [])

    def test_failed_prerequisite_is_preserved_not_rewritten_as_success(self):
        values = {**GOOD, "performance": "failure"}
        rows, diagnostics = capture_ci_evidence(values)
        self.assertEqual(rows[1]["conclusion"], "failure")
        self.assertEqual(diagnostics["capture_status"], "CAPTURED")
        self.assertEqual(diagnostics["inputs"]["prerequisite_results"]["performance"], "failure")

    def test_missing_result_is_captured_as_not_verified_with_diagnostics(self):
        values = {**GOOD, "repository": ""}
        rows, diagnostics = capture_ci_evidence(values)
        self.assertEqual(rows[2]["conclusion"], "NOT_VERIFIED")
        self.assertEqual(diagnostics["capture_status"], "CAPTURED_WITH_ERRORS")
        self.assertTrue(any("repository result is missing" in error for error in diagnostics["validation_errors"]))

    def test_invalid_run_url_and_sha_mismatch_are_diagnosed(self):
        values = {**GOOD, "url": "https://example.com/not-a-run", "bundle_sha": "b" * 40}
        rows, diagnostics = capture_ci_evidence(values)
        self.assertTrue(all(row["url"] == values["url"] for row in rows))
        self.assertEqual(diagnostics["capture_status"], "CAPTURED_WITH_ERRORS")
        joined = " ".join(diagnostics["validation_errors"])
        self.assertIn("GitHub HTTPS Actions run URL", joined)
        self.assertIn("head_sha must match bundle_sha", joined)

    def test_unrecognized_conclusion_fails_capture_diagnostics(self):
        rows, diagnostics = capture_ci_evidence({**GOOD, "tests": "success-ish"})
        self.assertEqual(rows[0]["conclusion"], "success-ish")
        self.assertEqual(diagnostics["capture_status"], "CAPTURED_WITH_ERRORS")
        self.assertTrue(any("tests result is missing or unrecognized" in e for e in diagnostics["validation_errors"]))


if __name__ == "__main__":
    unittest.main()


class NegativePathArtifactTests(unittest.TestCase):
    def test_generated_receipt_is_parseable_json(self):
        receipt = {
            "scenario": "required_performance_job_failure",
            "expected_ci_gate": "NOT_VERIFIED",
            "actual_ci_gate": "NOT_VERIFIED",
            "expected_release_decision": "HOLD",
            "actual_release_decision": "HOLD",
            "result": "PASS",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "negative-path-validation.json"
            output.write_text(
                json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            parsed = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(parsed["result"], "PASS")
        self.assertEqual(parsed["actual_ci_gate"], "NOT_VERIFIED")
        self.assertEqual(parsed["actual_release_decision"], "HOLD")
