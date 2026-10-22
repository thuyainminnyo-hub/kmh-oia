import base64
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from src.runtime_artifact_attestation import (
    Ed25519RuntimeArtifactAttestationVerifier, RuntimeArtifactAttestation,
    canonical_attestation_payload,
)


class Ed25519RuntimeArtifactAttestationVerifierTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
        self.private_key = Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw,
        )
        self.verifier = Ed25519RuntimeArtifactAttestationVerifier(
            {"build-key-1": self.public_key},
            allowed_issuers=("kmh-build-service",),
            allowed_subjects=("repo:thuyainminnyo-hub/kmh-oia:ref:refs/heads/main",),
            max_age_seconds=3600, clock=lambda: self.now,
        )
        self.attestation = RuntimeArtifactAttestation(
            classifier_sha256="a" * 64, policy_sha256="b" * 64,
            issuer="kmh-build-service",
            subject="repo:thuyainminnyo-hub/kmh-oia:ref:refs/heads/main",
            attestation_id="attestation-804-001", key_id="build-key-1",
            source_revision="c" * 40, build_run_id="987654321",
            issued_at="2026-10-21T11:30:00Z",
        )
        self.attestation = self.sign(self.attestation)

    def sign(self, attestation):
        signature = self.private_key.sign(canonical_attestation_payload(attestation))
        return replace(attestation, signature=base64.b64encode(signature).decode("ascii"))

    def test_valid_signed_attestation_is_accepted(self):
        self.assertTrue(self.verifier.verify(
            self.attestation, expected_classifier_sha256="a" * 64, expected_policy_sha256="b" * 64,
        ))

    def test_tampered_source_revision_invalidates_signature(self):
        tampered = replace(self.attestation, source_revision="d" * 40)
        self.assertFalse(self.verifier.verify(
            tampered, expected_classifier_sha256="a" * 64, expected_policy_sha256="b" * 64,
        ))

    def test_unknown_key_id_is_rejected(self):
        unknown = replace(self.attestation, key_id="unknown-key")
        self.assertFalse(self.verifier.verify(
            unknown, expected_classifier_sha256="a" * 64, expected_policy_sha256="b" * 64,
        ))

    def test_wrong_issuer_is_rejected(self):
        wrong = self.sign(replace(self.attestation, issuer="untrusted-builder", signature=""))
        self.assertFalse(self.verifier.verify(
            wrong, expected_classifier_sha256="a" * 64, expected_policy_sha256="b" * 64,
        ))

    def test_wrong_subject_is_rejected(self):
        wrong = self.sign(replace(self.attestation, subject="repo:attacker/project:ref:main", signature=""))
        self.assertFalse(self.verifier.verify(
            wrong, expected_classifier_sha256="a" * 64, expected_policy_sha256="b" * 64,
        ))

    def test_wrong_expected_artifact_digest_is_rejected(self):
        self.assertFalse(self.verifier.verify(
            self.attestation, expected_classifier_sha256="d" * 64, expected_policy_sha256="b" * 64,
        ))

    def test_malformed_signature_is_rejected(self):
        malformed = replace(self.attestation, signature="%%%not-base64%%%")
        self.assertFalse(self.verifier.verify(
            malformed, expected_classifier_sha256="a" * 64, expected_policy_sha256="b" * 64,
        ))

    def test_expired_statement_is_rejected_when_max_age_is_configured(self):
        older = replace(self.attestation, issued_at="2026-10-20T10:00:00Z", signature="")
        older = self.sign(older)
        self.assertFalse(self.verifier.verify(
            older, expected_classifier_sha256="a" * 64, expected_policy_sha256="b" * 64,
        ))

    def test_future_dated_statement_beyond_clock_skew_is_rejected(self):
        future = replace(self.attestation, issued_at="2026-10-21T13:00:00Z", signature="")
        future = self.sign(future)
        self.assertFalse(self.verifier.verify(
            future, expected_classifier_sha256="a" * 64, expected_policy_sha256="b" * 64,
        ))

    def test_constructor_rejects_malformed_public_key(self):
        with self.assertRaisesRegex(ValueError, "32 raw bytes"):
            Ed25519RuntimeArtifactAttestationVerifier(
                {"bad": b"short"}, allowed_issuers=("issuer",), allowed_subjects=("subject",),
            )

    def test_constructor_requires_explicit_trust_and_allowlists(self):
        with self.assertRaisesRegex(ValueError, "at least one trusted"):
            Ed25519RuntimeArtifactAttestationVerifier({}, allowed_issuers=("issuer",), allowed_subjects=("subject",))


if __name__ == "__main__":
    unittest.main()
