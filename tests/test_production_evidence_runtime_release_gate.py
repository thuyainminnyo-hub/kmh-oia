import base64
import hashlib
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from scripts.create_runtime_bundle_attestation import create_signed_runtime_bundle_attestation
from scripts.package_runtime_bundle import build_runtime_bundle
from src.live_operating_console import LiveOperatingConsole
from src.production_evidence_runtime import ProductionEvidenceRuntimeConfig, build_production_evidence_runtime
from src.runtime_bundle_attestation_io import write_runtime_bundle_attestation


class ReleaseAwareProductionFactoryTests(unittest.TestCase):
    class Adapter:
        provider_name = "test-provider"
        def fetch_receipt(self, source_record_id, execution_id):
            return None
        def verify_receipt(self, receipt):
            return False
        def match_execution(self, receipt, execution_id):
            return False

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "src").mkdir()
        (self.root / "src" / "runtime.py").write_text("VALUE = 817\n", encoding="utf-8")
        (self.root / "requirements.txt").write_text("cryptography==50.0.2\n", encoding="utf-8")
        self.revision = "a" * 40
        self.bundle = build_runtime_bundle(self.root, self.revision, self.root / "bundle.tar.gz")
        self.private = Ed25519PrivateKey.generate()
        self.public = self.private.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
        self.run_id = "123456789"
        self.artifact_id = "987654321"
        self.artifact_digest = "sha256:" + "b" * 64
        self.issuer = "kmh-release-signer-test"
        self.subject = "repo:thuyainminnyo-hub/kmh-oia:ref:refs/heads/main"
        env = {
            "KMH_OIA_ATTESTATION_PRIVATE_KEY_B64": base64.b64encode(self.private.private_bytes_raw()).decode("ascii"),
            "KMH_OIA_ATTESTATION_KEY_ID": "release-key-test",
            "KMH_OIA_ATTESTATION_ISSUER": self.issuer,
            "KMH_OIA_ATTESTATION_SUBJECT": self.subject,
            "KMH_OIA_ENVIRONMENT": "test",
        }
        attestation = create_signed_runtime_bundle_attestation(
            self.bundle, source_revision=self.revision, build_run_id=self.run_id,
            artifact_id=self.artifact_id, artifact_name="kmh-oia-runtime-bundle",
            artifact_digest=self.artifact_digest, environ=env,
        )
        self.attestation_path = self.root / "attestation.json"
        write_runtime_bundle_attestation(self.attestation_path, attestation)
        self.console = LiveOperatingConsole(date="2026-10-22")
        self.adapter = self.Adapter()

    def config(self, **changes):
        values = dict(
            sqlite_path=str(self.root / "replay.sqlite3"),
            allowed_source_providers=("test-provider",),
            runtime_bundle_path=str(self.bundle),
            runtime_source_root=str(self.root),
            runtime_attestation_path=str(self.attestation_path),
            expected_source_revision=self.revision,
            expected_build_run_id=self.run_id,
            expected_artifact_id=self.artifact_id,
            expected_artifact_name="kmh-oia-runtime-bundle",
            expected_artifact_digest=self.artifact_digest,
            trusted_release_public_keys={"release-key-test": self.public},
            allowed_release_issuers=(self.issuer,),
            allowed_release_subjects=(self.subject,),
        )
        values.update(changes)
        return ProductionEvidenceRuntimeConfig(**values)

    def test_factory_accepts_verified_bundle_and_attestation(self):
        bridge = build_production_evidence_runtime(self.console, config=self.config(), trusted_source_adapter=self.adapter)
        self.assertTrue(bridge.trusted_source_verifier.replay_store.health_check())

    def test_factory_rejects_tampered_bundle_before_runtime_startup(self):
        self.bundle.write_bytes(self.bundle.read_bytes() + b"tampered")
        with self.assertRaisesRegex(ValueError, "bundle or provenance did not verify"):
            build_production_evidence_runtime(self.console, config=self.config(), trusted_source_adapter=self.adapter)

    def test_partial_release_configuration_is_rejected(self):
        config = self.config(trusted_release_public_keys=None)
        with self.assertRaisesRegex(ValueError, "trusted public-key map"):
            build_production_evidence_runtime(self.console, config=config, trusted_source_adapter=self.adapter)

    def test_wrong_source_sha_is_rejected(self):
        config = self.config(expected_source_revision="c" * 40)
        with self.assertRaisesRegex(ValueError, "bundle or provenance did not verify"):
            build_production_evidence_runtime(self.console, config=config, trusted_source_adapter=self.adapter)

    def test_missing_key_or_issuer_allowlist_is_rejected(self):
        for changes, expected in (
            ({"trusted_release_public_keys": {}}, "trusted public-key map"),
            ({"allowed_release_issuers": ()}, "issuer allowlist"),
            ({"allowed_release_subjects": ()}, "subject allowlist"),
        ):
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, expected):
                build_production_evidence_runtime(self.console, config=self.config(**changes), trusted_source_adapter=self.adapter)


if __name__ == "__main__":
    unittest.main()
