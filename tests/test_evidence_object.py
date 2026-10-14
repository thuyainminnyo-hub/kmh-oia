import unittest
from dataclasses import FrozenInstanceError

from src.evidence_object import EvidenceObject


class EvidenceObjectTests(unittest.TestCase):
    def make_evidence(self, **overrides):
        values = {
            "evidence_id": "evidence:001",
            "kind": "runtime_trace",
            "source": "kmh-oia",
            "observed_at": "2026-10-14T08:30:00Z",
            "scope": "controlled-pilot",
            "source_revision": "abc1234",
            "artifact_ref": "trace:run-001",
            "run_id": "run-001",
        }
        values.update(overrides)
        return EvidenceObject(**values)

    def test_observed_evidence_requires_provenance_and_artifact_reference(self):
        evidence = self.make_evidence()
        self.assertEqual(evidence.validation_state, "OBSERVED")
        self.assertEqual(evidence.run_id, "run-001")

    def test_at_least_one_execution_reference_is_required(self):
        with self.assertRaisesRegex(ValueError, "execution reference"):
            self.make_evidence(run_id=None)

    def test_artifact_reference_or_digest_is_required(self):
        with self.assertRaisesRegex(ValueError, "artifact_ref or sha256_digest"):
            self.make_evidence(artifact_ref=None)

    def test_sha256_digest_must_have_exact_format(self):
        with self.assertRaisesRegex(ValueError, "64 lowercase hexadecimal"):
            self.make_evidence(artifact_ref=None, sha256_digest="not-a-digest")

    def test_timezone_is_required(self):
        with self.assertRaisesRegex(ValueError, "timezone offset"):
            self.make_evidence(observed_at="2026-10-14T08:30:00")

    def test_invalid_timestamp_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "ISO-8601"):
            self.make_evidence(observed_at="yesterday")

    def test_verified_state_requires_validation_reference(self):
        with self.assertRaisesRegex(ValueError, "validation_ref"):
            self.make_evidence(validation_state="VERIFIED")

    def test_outcome_linked_requires_validation_and_outcome_references(self):
        with self.assertRaisesRegex(ValueError, "outcome_ref"):
            self.make_evidence(
                validation_state="OUTCOME_LINKED",
                validation_ref="review:001",
            )

    def test_outcome_linked_accepts_explicit_references(self):
        evidence = self.make_evidence(
            validation_state="OUTCOME_LINKED",
            validation_ref="review:001",
            outcome_ref="outcome:001",
        )
        self.assertEqual(evidence.validation_state, "OUTCOME_LINKED")

    def test_record_is_immutable(self):
        evidence = self.make_evidence()
        with self.assertRaises(FrozenInstanceError):
            evidence.validation_state = "VERIFIED"

    def test_blank_required_fields_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "source_revision"):
            self.make_evidence(source_revision=" ")


if __name__ == "__main__":
    unittest.main()
