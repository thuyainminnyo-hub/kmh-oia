import base64
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from scripts.create_runtime_bundle_attestation import create_signed_runtime_bundle_attestation
from scripts.package_runtime_bundle import build_runtime_bundle
from src.live_operating_console import LiveOperatingConsole
from src.production_evidence_runtime import ProductionEvidenceRuntimeConfig
from src.trusted_source_receipt import TrustedSourceReceipt
from src.verified_production_evidence_runtime import build_verified_production_evidence_runtime


class MinimalAdapter:
    provider_name = "test-provider"

    def fetch_receipt(self, source_record_id, execution_id):
        return None

    def verify_receipt(self, receipt):
        return False

    def match_execution(self, receipt, execution_id):
        return False


class VerifiedProductionRuntimeIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "src").mkdir()
        (self.root / "src" / "runtime.py").write_text("VALUE = 1\n", encoding="utf-8")
        (self.root / "requirements.txt").write_text("cryptography==50.0.2\n", encoding="utf-8")
        self.revision = "a" * 40
        self.bundle = build_runtime_bundle(self.root, self.revision, self.root / "bundle.tar.gz")
        private_key = Ed25519PrivateKey.generate()
        self.public_key = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )
        self.key_id = "verified-runtime-test-key"
        self.issuer = "verified-runtime-test-issuer"
        self.subject = "repo:thuyainminnyo-hub/kmh-oia:ref:refs/heads/main"
        self.run_id = "12345"
        self.artifact_id = "67890"
        self.artifact_name = "kmh-oia-runtime-bundle"
        self.artifact_digest = "sha256:" + "b" * 64
        env = {
            "KMH_OIA_ATTESTATION_PRIVATE_KEY_B64": base64.b64encode(
                private_key.private_bytes_raw()
            ).decode("ascii"),
            "KMH_OIA_ATTESTATION_KEY_ID": self.key_id,
            "KMH_OIA_ATTESTATION_ISSUER": self.issuer,
            "KMH_OIA_ATTESTATION_SUBJECT": self.subject,
            "KMH_OIA_ENVIRONMENT": "test",
        }
        attestation = create_signed_runtime_bundle_attestation(
            self.bundle,
            source_revision=self.revision,
            build_run_id=self.run_id,
            artifact_id=self.artifact_id,
            artifact_name=self.artifact_name,
            artifact_digest=self.artifact_digest,
            environ=env,
        )
        from src.runtime_bundle_attestation_io import write_runtime_bundle_attestation
        self.attestation_path = write_runtime_bundle_attestation(self.root / "attestation.json", attestation)
        self.console = LiveOperatingConsole(date="2026-10-22")
        self.config = ProductionEvidenceRuntimeConfig(
            str(self.root / "evidence-replay.sqlite3"), ("test-provider",)
        )

    def build(self, **overrides):
        args = {
            "console": self.console,
            "config": self.config,
            "trusted_source_adapter": MinimalAdapter(),
            "bundle_path": self.bundle,
            "attestation_path": self.attestation_path,
            "runtime_source_root": self.root,
            "expected_source_revision": self.revision,
            "expected_build_run_id": self.run_id,
            "expected_artifact_id": self.artifact_id,
            "expected_artifact_name": self.artifact_name,
            "expected_artifact_digest": self.artifact_digest,
            "trusted_public_keys": {self.key_id: self.public_key},
            "allowed_issuers": (self.issuer,),
            "allowed_subjects": (self.subject,),
        }
        args.update(overrides)
        return build_verified_production_evidence_runtime(**args)

    def test_runtime_is_constructed_after_valid_bundle_and_provenance(self):
        bridge = self.build()
        self.assertTrue(bridge.trusted_source_verifier.replay_store.health_check())
        self.assertEqual(bridge.trusted_source_verifier.allowed_providers, frozenset({"test-provider"}))

    def test_invalid_source_or_artifact_metadata_rejects_before_runtime_construction(self):
        with self.assertRaises(ValueError):
            self.build(expected_source_revision="c" * 40)
        with self.assertRaises(ValueError):
            self.build(expected_artifact_id="99999")

    def test_wrong_trust_root_rejects_before_runtime_construction(self):
        unrelated_key = Ed25519PrivateKey.generate().public_key().public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )
        with self.assertRaises(ValueError):
            self.build(trusted_public_keys={self.key_id: unrelated_key})

    def test_tampered_bundle_rejects_before_runtime_construction(self):
        original = self.bundle.read_bytes()
        self.bundle.write_bytes(original + b"tamper")
        with self.assertRaises(ValueError):
            self.build()



    def test_verified_release_metadata_is_forwarded_into_production_startup_gate(self):
        from unittest.mock import patch

        with patch(
            "src.verified_production_evidence_runtime.build_production_evidence_runtime",
            return_value="constructed",
        ) as inner:
            result = self.build()
        self.assertEqual(result, "constructed")
        config = inner.call_args.kwargs["config"]
        self.assertTrue(config.require_signed_release_bundle)
        self.assertEqual(config.runtime_bundle_path, str(self.bundle))
        self.assertEqual(config.runtime_source_root, str(self.root))
        self.assertEqual(config.runtime_attestation_path, str(self.attestation_path)
        self.assertEqual(config.expected_source_revision, self.revision)
        self.assertEqual(config.expected_build_run_id, self.run_id)
        self.assertEqual(config.expected_artifact_id, self.artifact_id)
        self.assertEqual(config.expected_artifact_name, self.artifact_name)
        self.assertEqual(config.expected_artifact_digest, self.artifact_digest)
        self.assertEqual(config.trusted_release_public_keys, {self.key_id: self.public_key})
        self.assertEqual(config.allowed_release_issuers, (self.issuer,))
        self.assertEqual(config.allowed_release_subjects, (self.subject,))

if __name__ == "__main__":
    unittest.main()
