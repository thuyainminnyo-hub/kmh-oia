import json
import tempfile
import unittest
from pathlib import Path

from src.production_readiness import (
    PreDeploymentHealthController,
    ProductionEnvironmentValidator,
    ReleaseCandidateLoader,
)


class Stage14ProductionReadinessTests(unittest.TestCase):
    def test_release_candidate_loader_requires_manifest_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "release.json"
            path.write_text(json.dumps({"release_id": "rc-1", "commit": "abc123"}), encoding="utf-8")
            release = ReleaseCandidateLoader().load(path)
            self.assertEqual("rc-1", release["release_id"])
            self.assertEqual("abc123", release["commit"])

    def test_environment_validator_reports_failed_prerequisite(self):
        report = ProductionEnvironmentValidator().validate(
            environment="staging",
            release={"release_id": "rc-1", "commit": "abc123"},
            dependencies=["python==3.12", "runtime"],
        )
        self.assertTrue(report.passed)

        blocked = ProductionEnvironmentValidator().validate(
            environment="",
            release={"release_id": "rc-1", "commit": "abc123"},
            dependencies=["runtime"],
        )
        self.assertFalse(blocked.passed)
        self.assertEqual(["environment"], [check.name for check in blocked.checks if not check.passed])

    def test_health_controller_blocks_failed_report(self):
        report = ProductionEnvironmentValidator().validate(
            environment="",
            release={"release_id": "rc-1", "commit": "abc123"},
            dependencies=["runtime"],
        )
        with self.assertRaisesRegex(RuntimeError, "pre-deployment health gate blocked"):
            PreDeploymentHealthController().gate(report)


if __name__ == "__main__":
    unittest.main()
