import os
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_prerequisite_results.py"


class PrerequisiteResultTests(unittest.TestCase):
    def run_check(self, overrides=None):
        env = os.environ.copy()
        env.update(
            {
                "TESTS_RESULT": "success",
                "PERFORMANCE_RESULT": "success",
                "REPOSITORY_RESULT": "success",
            }
        )
        if overrides:
            env.update(overrides)
        return subprocess.run(
            [sys.executable, str(SCRIPT)],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_all_success_results_pass(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("All required prerequisite jobs succeeded.", result.stdout)

    def test_failure_result_fails_closed(self):
        result = self.run_check({"TESTS_RESULT": "failure"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("tests", result.stderr)
        self.assertIn("failure", result.stderr)

    def test_skipped_result_fails_closed(self):
        result = self.run_check({"PERFORMANCE_RESULT": "skipped"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("performance-evidence", result.stderr)

    def test_missing_result_fails_closed(self):
        result = self.run_check({"REPOSITORY_RESULT": ""})
        self.assertEqual(result.returncode, 1)
        self.assertIn("repository-validation", result.stderr)


if __name__ == "__main__":
    unittest.main()
