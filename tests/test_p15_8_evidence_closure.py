"""Tests for the P15.8 evidence closure gate."""

import unittest

from src.p15_7_evidence import EvidenceArtifact, EvidenceBundleBuilder
from src.p15_8_evidence_closure import EvidenceClosureController


def artifact(name: str) -> EvidenceArtifact:
    return EvidenceArtifact(
        name=name,
        environment="staging",
        observed_at="2026-10-02T00:00:00Z",
        source=f"operator://{name}",
        value=f"evidence-{name}",
    )


class EvidenceClosureControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = EvidenceBundleBuilder()
        self.controller = EvidenceClosureController()

    def bundle(self, names: tuple[str, ...]):
        return self.builder.build(
            release_id="release-15-8",
            artifacts=tuple(artifact(name) for name in names),
        )

    def test_incomplete_bundle_reports_missing_categories(self) -> None:
        bundle = self.bundle(("telemetry", "performance"))
        state = self.controller.evaluate(
            bundle,
            expected_release_id="release-15-8",
        )

        self.assertFalse(state.complete)
        self.assertEqual(
            state.missing,
            ("rollback_drill", "authorization", "incident_exercise"),
        )

    def test_complete_bundle_closes_evidence_gate(self) -> None:
        bundle = self.bundle(EvidenceClosureController.REQUIRED_NAMES)
        state = self.controller.evaluate(
            bundle,
            expected_release_id="release-15-8",
        )

        self.assertTrue(state.complete)
        self.assertEqual(state.missing, ())
        self.controller.validate(state)

    def test_release_mismatch_is_rejected(self) -> None:
        bundle = self.bundle(EvidenceClosureController.REQUIRED_NAMES)

        with self.assertRaises(ValueError):
            self.controller.evaluate(
                bundle,
                expected_release_id="different-release",
            )

    def test_blank_expected_release_is_rejected(self) -> None:
        bundle = self.bundle(EvidenceClosureController.REQUIRED_NAMES)

        with self.assertRaises(ValueError):
            self.controller.evaluate(bundle, expected_release_id="   ")

    def test_incomplete_state_cannot_be_validated(self) -> None:
        bundle = self.bundle(("telemetry",))
        state = self.controller.evaluate(
            bundle,
            expected_release_id="release-15-8",
        )

        with self.assertRaises(RuntimeError):
            self.controller.validate(state)


if __name__ == "__main__":
    unittest.main()
