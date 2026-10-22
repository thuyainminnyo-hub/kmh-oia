import base64
import hashlib
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from scripts.create_runtime_bundle_attestation import create_signed_runtime_bundle_attestation
from scripts.package_runtime_bundle import build_runtime_bundle
from scripts.verify_runtime_bundle_release import RuntimeBundleReleaseRejected, verify_runtime_bundle_release
from src.runtime_bundle_attestation_io import write_runtime_bundle_attestation


class RuntimeBundleReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "src").mkdir()
        (self.root / "src" / "runtime.py").write_text("VALUE = 816\n", encoding="utf-8")
        (self.root / "requirements.txt").write_text("cryptography==50.0.2\n", encoding="utf-8")
        self.revision = "a" * 40
        self.bundle = build_runtime_bundle(self.root, self.revision, self.root / "bundle.tar.gz")
        self.private_key = Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw,
        )
        self.key_id = "release-key-test"
        self.issuer = "kmh-release-signer-test"
        self.subject = "repo:thuyainminnyo-hub/kmh-oia:ref:refs/heads/main"
        self.artifact_id = "123456789"
        self.run_id = "987654321"
        self.artifact_digest = "sha256:" + "b" * 64
        self.attestation_path = self.root / "release-attestation.json"
        env = {
            "KMH_OIA_ATTESTATION_PRIVATE_KEY_B64": base64.b64encode(self.private_key.private_bytes_raw()).decode("ascii"),
            "KMH_OIA_ATTESTATION_KEY_ID": self.key_id, "KMH_OIA_ATTESTATION_ISSUER": self.issuer,
            "KMH_OIA_ATTESTATION_SUBJECT": self.subject, "KMH_OIA_ENVIRONMENT": "test",
        }
        attestation = create_signed_runtime_bundle_attestation(
            self.bundle, source_revision=self.revision, build_run_id=self.run_id,
            artifact_id=self.artifact_id, artifact_name="kmh-oia-runtime-bundle",
            artifact_digest=self.artifact_digest, environ=env,
        )
        write_runtime_bundle_attestation(self.attestation_path, attestation)

    def verify(self, **overrides):
        args = {
            "expected_source_revision": self.revision, "expected_build_run_id": self.run_id,
            "expected_artifact_id": self.artifact_id, "expected_artifact_name": "kmh-oia-runtime-bundle",
            "expected_artifact_digest": self.artifact_digest, "trusted_public_keys": {self.key_id: self.public_key},
            "allowed_issuers": (self.issuer,), "allowed_subjects": (self.subject,),
            "max_age_seconds": 3600, "max_clock_skew_seconds": 60,
        }
        args.update(overrides)
        return verify_runtime_bundle_release(self.bundle, self.attestation_path, **args)

    def test_valid_signed_bundle_passes_consumer_gate(self):
        result = self.verify()
        self.assertEqual(result["source_revision"], self.revision)
        self.assertEqual(result["build_run_id"], self.run_id)
        self.assertEqual(result["artifact_id"], self.artifact_id)
        self.assertEqual(result["bundle_sha256"], hashlib.sha256(self.bundle.read_bytes()).hexdigest())
        self.assertGreaterEqual(result["files_verified"], 2)

    def test_wrong_key_issuer_subject_or_expected_metadata_is_rejected(self):
        bad_key = Ed25519PrivateKey.generate().public_key().public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw,
        )
        mutations = (
            {"trusted_public_keys": {self.key_id: bad_key}},
            {"allowed_issuers": ("untrusted-issuer",)},
            {"allowed_subjects": ("repo:attacker/repo:ref:refs/heads/main",)},
            {"expected_build_run_id": "987654322"},
            {"expected_artifact_id": "123456788"},
            {"expected_artifact_digest": "sha256:" + "c" * 64},
            {"expected_source_revision": "c" * 40},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(RuntimeBundleReleaseRejected):
                self.verify(**mutation)

    def test_tampered_bundle_or_signature_is_rejected(self):
        original = self.bundle.read_bytes()
        self.bundle.write_bytes(original + b"tamper")
        with self.assertRaises(RuntimeBundleReleaseRejected):
            self.verify()
        self.bundle.write_bytes(original)
        import json
        data = json.loads(self.attestation_path.read_text(encoding="utf-8"))
        data["signature"] = "AAAA"
        self.attestation_path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(RuntimeBundleReleaseRejected):
            self.verify()

    def test_missing_public_trust_root_fails_closed(self):
        with self.assertRaisesRegex(RuntimeBundleReleaseRejected, "could not be validated"):
            self.verify(trusted_public_keys={})


if __name__ == "__main__":
    unittest.main()
