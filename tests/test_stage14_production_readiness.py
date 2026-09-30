import json
import tempfile
import unittest
from pathlib import Path

from src.production_readiness import (
    ControlledDeploymentController,
    PreDeploymentHealthController,
    ProductionEnvironmentValidator,
    ProductionHealthGate,
    ReadinessReport,
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

    def test_controlled_deployment_starts_at_canary_and_promotes_progressively(self):
        readiness = ReadinessReport(True, ())
        controller = ControlledDeploymentController()

        state = controller.start(release_id="rc-1", readiness=readiness, traffic_stages=(5, 25, 100))
        self.assertEqual((5, "canary"), (state.traffic_percent, state.phase))

        state = controller.promote(state, health_passed=True, traffic_stages=(5, 25, 100))
        self.assertEqual((25, "staged"), (state.traffic_percent, state.phase))

        state = controller.promote(state, health_passed=True, traffic_stages=(5, 25, 100))
        self.assertEqual((100, "promoted"), (state.traffic_percent, state.phase))

    def test_controlled_deployment_blocks_failed_health_promotion(self):
        readiness = ReadinessReport(True, ())
        state = ControlledDeploymentController().start(
            release_id="rc-1",
            readiness=readiness,
            traffic_stages=(5, 100),
        )

        with self.assertRaisesRegex(RuntimeError, "failed health gate"):
            ControlledDeploymentController().promote(
                state,
                health_passed=False,
                traffic_stages=(5, 100),
            )

    def test_controlled_deployment_rollback_is_deterministic(self):
        readiness = ReadinessReport(True, ())
        controller = ControlledDeploymentController()
        state = controller.start(release_id="rc-1", readiness=readiness, traffic_stages=(5, 100))

        rolled_back = controller.rollback(state, reason="health regression")
        self.assertEqual((0, "rolled_back", "health regression"), (
            rolled_back.traffic_percent,
            rolled_back.phase,
            rolled_back.reason,
        ))

    def test_controlled_deployment_requires_valid_traffic_plan(self):
        readiness = ReadinessReport(True, ())
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            ControlledDeploymentController().start(
                release_id="rc-1",
                readiness=readiness,
                traffic_stages=(25, 10, 100),
            )

    def test_production_health_gate_passes_only_when_all_required_components_pass(self):
        checks = {name: True for name in ProductionHealthGate.REQUIRED_COMPONENTS}
        report = ProductionHealthGate().assess(checks)
        self.assertTrue(report.passed)
        self.assertEqual(
            list(ProductionHealthGate.REQUIRED_COMPONENTS),
            [check.name for check in report.checks],
        )

    def test_production_health_gate_blocks_missing_component_evidence(self):
        checks = {name: True for name in ProductionHealthGate.REQUIRED_COMPONENTS}
        checks["observability"] = False

        report = ProductionHealthGate().assess(checks)
        self.assertFalse(report.passed)
        self.assertEqual(["observability"], [check.name for check in report.checks if not check.passed])

        with self.assertRaisesRegex(RuntimeError, "observability"):
            ProductionHealthGate().gate(report)

    def test_production_health_gate_treats_missing_checks_as_failed(self):
        report = ProductionHealthGate().assess({"service": True, "api": True})
        self.assertFalse(report.passed)
        self.assertEqual(
            len(ProductionHealthGate.REQUIRED_COMPONENTS) - 2,
            len([check for check in report.checks if not check.passed]),
        )


if __name__ == "__main__":
    unittest.main()
