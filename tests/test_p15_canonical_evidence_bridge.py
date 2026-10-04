"""Focused tests for the canonical P15 evidence bridge."""

import hashlib
import unittest

from src.operational_evidence_package import OperationalEvidencePackage
from src.p15_8_evidence_closure import EvidenceClosure
from src.p15_7_evidence import EvidenceBundleBuilder
from src.stage15_handoff import Stage15HandoffController
from src.p15_canonical_evidence_bridge import (
    BridgeInput,
    CanonicalEvidenceBridgeAdapter,
    EvidenceReference,
    ReleaseDeploymentMapping,
    Stage14EvidenceMapping,
    verify_sha256,
)


class CanonicalEvidenceBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = CanonicalEvidenceBridgeAdapter()
        self.release = "release-15-bridge"
        self.deployment = "deployment-15-bridge"
        self.refs = tuple(
            EvidenceReference(
                reference_id=f"ref-{field}",
                environment="staging",
                observed_at="2026-10-03T00:00:00Z",
                source=f"operator://{field}",
                value=f"evidence-{field}",
            )
            for field in self.adapter.REQUIRED_FIELDS
        )
        self.mappings = tuple(
            Stage14EvidenceMapping(
                field=field,
                evidence_reference_ids=(f"ref-{field}",),
                applicability="explicitly supplied for this bridge test",
                rationale=f"approved mapping reference for {field}",
            )
            for field in self.adapter.REQUIRED_FIELDS
        )

    def bridge(self, **overrides) -> BridgeInput:
        values = dict(
            release_id=self.release,
            deployment_id=self.deployment,
            release_deployment_mappings=(
                ReleaseDeploymentMapping(self.release, self.deployment),
            ),
            closure=EvidenceClosure(self.release, True),
            evidence_references=self.refs,
            stage14_mapping=self.mappings,
            production_boundary_acknowledged=True,
        )
        values.update(overrides)
        return BridgeInput(**values)

    def test_br_01_builds_complete_package_from_explicit_inputs(self) -> None:
        package = self.adapter.build_package(self.bridge())
        self.assertIsInstance(package, OperationalEvidencePackage)
        self.assertTrue(package.complete)
        self.assertEqual(package.deployment_id, self.deployment)
        self.assertEqual(len(package.items), 14)

    def test_br_02_missing_release_deployment_mapping_blocks(self) -> None:
        with self.assertRaises(RuntimeError):
            self.adapter.build_package(self.bridge(release_deployment_mappings=()))

    def test_br_03_ambiguous_release_deployment_mapping_blocks(self) -> None:
        mappings = (
            ReleaseDeploymentMapping(self.release, self.deployment),
            ReleaseDeploymentMapping(self.release, "deployment-other"),
        )
        with self.assertRaises(RuntimeError):
            self.adapter.build_package(self.bridge(release_deployment_mappings=mappings))

    def test_br_04_release_mismatch_blocks(self) -> None:
        with self.assertRaises(ValueError):
            self.adapter.build_package(
                self.bridge(
                    release_id="different-release",
                    closure=EvidenceClosure("different-release", True),
                )
            )

    def test_br_05_incomplete_closure_blocks(self) -> None:
        with self.assertRaises(RuntimeError):
            self.adapter.build_package(
                self.bridge(
                    closure=EvidenceClosure(
                        self.release,
                        False,
                        EvidenceBundleBuilder.REQUIRED_NAMES,
                        "incomplete",
                    )
                )
            )

    def test_br_06_missing_stage14_evidence_reference_blocks(self) -> None:
        mappings = tuple(
            Stage14EvidenceMapping(
                field=field,
                evidence_reference_ids=(),
                applicability="explicitly supplied",
                rationale="missing reference must block",
            )
            if field == "telemetry"
            else mapping
            for field, mapping in zip(self.adapter.REQUIRED_FIELDS, self.mappings)
        )
        with self.assertRaises(RuntimeError):
            self.adapter.build_package(self.bridge(stage14_mapping=mappings))

    def test_br_07_missing_provenance_blocks(self) -> None:
        refs = list(self.refs)
        refs[0] = EvidenceReference(
            reference_id=refs[0].reference_id,
            environment="",
            observed_at=refs[0].observed_at,
            source=refs[0].source,
            value=refs[0].value,
        )
        with self.assertRaises(ValueError):
            self.adapter.build_package(self.bridge(evidence_references=tuple(refs)))

    def test_br_08_unsupported_mapping_blocks(self) -> None:
        mappings = self.mappings[:-1] + (
            Stage14EvidenceMapping(
                field="unsupported_field",
                evidence_reference_ids=("ref-telemetry",),
                applicability="explicit",
                rationale="unsupported field must block",
            ),
        )
        with self.assertRaises(RuntimeError):
            self.adapter.build_package(self.bridge(stage14_mapping=mappings))

    def test_br_09_conditional_mapping_without_applicability_blocks(self) -> None:
        mappings = list(self.mappings)
        mappings[0] = Stage14EvidenceMapping(
            field="telemetry",
            evidence_reference_ids=("ref-telemetry",),
            applicability="",
            rationale="conditional mapping without applicability must block",
        )
        with self.assertRaises(RuntimeError):
            self.adapter.build_package(self.bridge(stage14_mapping=tuple(mappings)))

    def test_br_10_false_boundary_acknowledgement_blocks(self) -> None:
        with self.assertRaises(RuntimeError):
            self.adapter.build_package(
                self.bridge(production_boundary_acknowledged=False)
            )

    def test_br_11_non_boolean_boundary_acknowledgement_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.adapter.build_package(
                self.bridge(production_boundary_acknowledged="yes")
            )

    def test_br_12_complete_package_and_acknowledgement_enable_repository_handoff(self) -> None:
        package = self.adapter.build_package(self.bridge())
        handoff = Stage15HandoffController().prepare(
            package,
            production_boundary_acknowledged=True,
        )
        self.assertTrue(handoff.ready)
        self.assertEqual(handoff.phase, "ready")

    def test_br_13_handoff_ready_is_not_production_certification(self) -> None:
        package = self.adapter.build_package(self.bridge())
        handoff = Stage15HandoffController().prepare(
            package,
            production_boundary_acknowledged=True,
        )
        self.assertIn("production execution is not certified", handoff.reason)

    def test_br_14_sha256_matching_supplied_bytes_passes(self) -> None:
        content = b"bridge-integrity"
        digest = hashlib.sha256(content).hexdigest()
        self.assertTrue(verify_sha256(content, digest))

    def test_br_15_sha256_mismatch_fails_integrity_verification(self) -> None:
        content = b"bridge-integrity"
        digest = hashlib.sha256(b"tampered").hexdigest()
        self.assertFalse(verify_sha256(content, digest))


if __name__ == "__main__":
    unittest.main()
