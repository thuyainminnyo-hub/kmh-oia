import hashlib
import tempfile
import unittest
from pathlib import Path

from src.runtime_artifact_attestation import RuntimeArtifactAttestation
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


if __name__ == "__main__":
    unittest.main()
