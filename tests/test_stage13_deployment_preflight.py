import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.deployment_preflight as preflight


class Stage13DeploymentPreflightTests(unittest.TestCase):
    def test_repository_preflight_passes_for_current_repository(self):
        self.assertEqual(preflight.validate_repository(), [])

    def test_missing_required_path_is_reported(self):
        missing = Path("missing-stage13-required-path")
        with patch.object(preflight, "REQUIRED_PATHS", (missing,)):
            failures = preflight.validate_repository()
        self.assertEqual(failures, [f"missing required path: {missing}"])

    def test_source_compilation_failure_is_reported(self):
        with patch.object(preflight, "REQUIRED_PATHS", (Path("."),)), patch.object(
            preflight.compileall, "compile_dir", return_value=False
        ):
            failures = preflight.validate_repository()
        self.assertEqual(failures, ["source compilation failed"])


if __name__ == "__main__":
    unittest.main()
