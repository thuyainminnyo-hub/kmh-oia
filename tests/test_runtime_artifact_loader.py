import base64
import hashlib
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from src.runtime_artifact_attestation import (
    Ed25519RuntimeArtifactAttestationVerifier,
    RuntimeArtifactAttestation,
    canonical_attestation_payload,
)
from src.runtime_artifact_loader import (
    RuntimeArtifactLoadError, verify_and_load_runtime_artifacts,
    verify_and_load_runtime_artifacts_from_bytes,
)


class AcceptingTestVerifier:
    def __init__(self, expected_issuer="test-ci"):
        self.expected_issuer = expected_issuer
        self.calls = 0

    def verify(self, attestation, *, expected_classifier_sha256, expected_policy_sha256):
        self.calls += 1
        return (
            attestation.issuer == self.expected_issuer
            and attestation.classifier_sha256 == expected_classifier_sha256
            and attestation.policy_sha256 == expected_policy_sha256
        )


class RuntimeArtifactLoaderTests(unittest.TestCase):
    def make_attestation(self, classifier_bytes, policy_bytes):
        return RuntimeArtifactAttestation(
            classifier_sha256=hashlib.sha256(classifier_bytes).hexdigest(),
            policy_sha256=hashlib.sha256(policy_bytes).hexdigest(),
            issuer="test-ci", subject="unit-test-runtime", attestation_id="loader-test",
        )

    def test_loaders_receive_exact_verified_byte_snapshots(self):
        classifier_bytes, policy_bytes = b"classifier model bytes", b"policy model bytes"
        attestation = self.make_attestation(classifier_bytes, policy_bytes)
        loaded = verify_and_load_runtime_artifacts_from_bytes(
            classifier_bytes, policy_bytes, attestation=attestation, verifier=AcceptingTestVerifier(),
            classifier_loader=lambda payload: {"bytes": payload},
            policy_loader=lambda payload: {"bytes": payload},
        )
        self.assertEqual(loaded.classifier["bytes"], classifier_bytes)
        self.assertEqual(loaded.policy["bytes"], policy_bytes)
        self.assertTrue(loaded.verify_integrity())

    def test_bad_signature_or_digest_blocks_both_loaders(self):
        classifier_bytes, policy_bytes = b"classifier model bytes", b"policy model bytes"
        attestation = self.make_attestation(classifier_bytes, policy_bytes)
        calls = []
        with self.assertRaises(RuntimeArtifactLoadError):
            verify_and_load_runtime_artifacts_from_bytes(
                classifier_bytes + b"tamper", policy_bytes, attestation=attestation,
                verifier=AcceptingTestVerifier(),
                classifier_loader=lambda payload: calls.append("classifier"),
                policy_loader=lambda payload: calls.append("policy"),
            )
        self.assertEqual(calls, [])

    def test_unknown_issuer_blocks_loader_callbacks(self):
        classifier_bytes, policy_bytes = b"classifier", b"policy"
        attestation = self.make_attestation(classifier_bytes, policy_bytes)
        calls = []
        with self.assertRaises(RuntimeArtifactLoadError):
            verify_and_load_runtime_artifacts_from_bytes(
                classifier_bytes, policy_bytes, attestation=attestation,
                verifier=AcceptingTestVerifier(expected_issuer="approved-builder"),
                classifier_loader=lambda payload: calls.append("classifier"),
                policy_loader=lambda payload: calls.append("policy"),
            )
        self.assertEqual(calls, [])

    def test_file_loader_reads_once_then_passes_bytes_not_path(self):
        classifier_bytes, policy_bytes = b"classifier-on-disk", b"policy-on-disk"
        attestation = self.make_attestation(classifier_bytes, policy_bytes)
        verifier = AcceptingTestVerifier()
        with tempfile.TemporaryDirectory() as directory:
            classifier_path = Path(directory) / "classifier.bin"
            policy_path = Path(directory) / "policy.bin"
            classifier_path.write_bytes(classifier_bytes)
            policy_path.write_bytes(policy_bytes)
            loaded = verify_and_load_runtime_artifacts(
                classifier_path, policy_path, attestation=attestation, verifier=verifier,
                classifier_loader=lambda payload: payload, policy_loader=lambda payload: payload,
            )
        self.assertEqual(loaded.classifier, classifier_bytes)
        self.assertEqual(loaded.policy, policy_bytes)

    def test_empty_artifact_is_rejected(self):
        with self.assertRaisesRegex(RuntimeArtifactLoadError, "missing or invalid"):
            verify_and_load_runtime_artifacts_from_bytes(
                b"", b"policy", attestation=self.make_attestation(b"x", b"policy"),
                verifier=AcceptingTestVerifier(), classifier_loader=lambda p: p, policy_loader=lambda p: p,
            )


    def test_ed25519_signature_and_measured_bytes_are_bound_before_load(self):
        classifier_bytes, policy_bytes = b"real classifier artifact payload", b"real policy artifact payload"
        classifier_digest = hashlib.sha256(classifier_bytes).hexdigest()
        policy_digest = hashlib.sha256(policy_bytes).hexdigest()
        now = datetime(2026, 10, 21, 14, 0, tzinfo=timezone.utc)
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw,
        )
        statement = RuntimeArtifactAttestation(
            classifier_sha256=classifier_digest, policy_sha256=policy_digest,
            issuer="kmh-ci-issuer", subject="repo:thuyainminnyo-hub/kmh-oia:ref:main",
            attestation_id="loader-ed25519-integration", key_id="test-key-1",
            source_revision="a" * 40, build_run_id="run-123",
            issued_at=now.isoformat().replace("+00:00", "Z"),
        )
        statement = replace(statement, signature=base64.b64encode(
            private_key.sign(canonical_attestation_payload(statement))
        ).decode("ascii"))
        verifier = Ed25519RuntimeArtifactAttestationVerifier(
            {"test-key-1": public_key},
            allowed_issuers=("kmh-ci-issuer",),
            allowed_subjects=("repo:thuyainminnyo-hub/kmh-oia:ref:main",),
            max_age_seconds=3600, clock=lambda: now,
        )
        loaded = verify_and_load_runtime_artifacts_from_bytes(
            classifier_bytes, policy_bytes, attestation=statement, verifier=verifier,
            classifier_loader=lambda payload: {"loaded_bytes": payload},
            policy_loader=lambda payload: {"loaded_bytes": payload},
        )
        self.assertEqual(loaded.classifier["loaded_bytes"], classifier_bytes)
        self.assertEqual(loaded.policy["loaded_bytes"], policy_bytes)
        self.assertTrue(loaded.verify_integrity())

    def test_ed25519_loader_rejects_mutated_payload_before_any_loader_runs(self):
        classifier_bytes, policy_bytes = b"trusted classifier payload", b"trusted policy payload"
        classifier_digest = hashlib.sha256(classifier_bytes).hexdigest()
        policy_digest = hashlib.sha256(policy_bytes).hexdigest()
        now = datetime(2026, 10, 21, 14, 0, tzinfo=timezone.utc)
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw,
        )
        statement = RuntimeArtifactAttestation(
            classifier_sha256=classifier_digest, policy_sha256=policy_digest,
            issuer="kmh-ci-issuer", subject="repo:thuyainminnyo-hub/kmh-oia:ref:main",
            attestation_id="loader-ed25519-tamper", key_id="test-key-2",
            source_revision="b" * 40, build_run_id="run-456",
            issued_at=now.isoformat().replace("+00:00", "Z"),
        )
        statement = replace(statement, signature=base64.b64encode(
            private_key.sign(canonical_attestation_payload(statement))
        ).decode("ascii"))
        verifier = Ed25519RuntimeArtifactAttestationVerifier(
            {"test-key-2": public_key},
            allowed_issuers=("kmh-ci-issuer",),
            allowed_subjects=("repo:thuyainminnyo-hub/kmh-oia:ref:main",),
            max_age_seconds=3600, clock=lambda: now,
        )
        calls = []
        with self.assertRaisesRegex(RuntimeArtifactLoadError, "verification failed closed"):
            verify_and_load_runtime_artifacts_from_bytes(
                classifier_bytes + b"mutated", policy_bytes, attestation=statement, verifier=verifier,
                classifier_loader=lambda payload: calls.append("classifier"),
                policy_loader=lambda payload: calls.append("policy"),
            )
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
