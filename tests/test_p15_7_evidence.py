import unittest

from src.p15_7_evidence import EvidenceArtifact, EvidenceBundleBuilder


class P157EvidenceBundleTests(unittest.TestCase):
    def test_build_requires_provenance_fields(self):
        builder = EvidenceBundleBuilder()
        artifact = EvidenceArtifact("telemetry", "staging", "2026-10-02T04:00:00Z", "run-1", "healthy=true")

        bundle = builder.build(release_id="rel-15-7", artifacts=(artifact,))

        self.assertEqual(bundle.release_id, "rel-15-7")
        self.assertEqual(bundle.artifacts, (artifact,))

    def test_duplicate_artifacts_are_rejected(self):
        builder = EvidenceBundleBuilder()
        artifact = EvidenceArtifact("telemetry", "staging", "2026-10-02T04:00:00Z", "run-1", "healthy=true")

        with self.assertRaises(ValueError):
            builder.build(release_id="rel-15-7", artifacts=(artifact, artifact))

    def test_missing_required_operational_evidence_is_rejected(self):
        builder = EvidenceBundleBuilder()
        artifact = EvidenceArtifact("telemetry", "staging", "2026-10-02T04:00:00Z", "run-1", "healthy=true")
        bundle = builder.build(release_id="rel-15-7", artifacts=(artifact,))

        with self.assertRaises(RuntimeError):
            builder.require_names(bundle)

    def test_complete_required_operational_evidence_is_accepted(self):
        builder = EvidenceBundleBuilder()
        artifacts = tuple(
            EvidenceArtifact(name, "staging", "2026-10-02T04:00:00Z", "run-1", "supplied")
            for name in builder.REQUIRED_NAMES
        )

        bundle = builder.build(release_id="rel-15-7", artifacts=artifacts)

        builder.require_names(bundle)


if __name__ == "__main__":
    unittest.main()
