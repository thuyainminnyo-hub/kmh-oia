import base64
import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from src.production_artifact_trust import (
    ProductionArtifactTrustConfigError, load_production_artifact_trust_config,
    load_production_runtime_artifacts,
)
from src.runtime_artifact_attestation import RuntimeArtifactAttestation, canonical_attestation_payload


class ProductionArtifactTrustTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.private_key = Ed25519PrivateKey.generate()
        self.public_bytes = self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw,
        )
        self.classifier_bytes = b"production-classifier-payload"
        self.policy_bytes = b"production-policy-payload"
        self.source_revision = "d" * 40
        self.env = {
            "KMH_OIA_ENVIRONMENT": "production",
            "KMH_OIA_ATTESTATION_TRUSTED_PUBLIC_KEYS_JSON": json.dumps({"prod-signing-key-2026": base64.b64encode(self.public_bytes).decode("ascii")}),
            "KMH_OIA_ATTESTATION_ALLOWED_ISSUERS": "kmh-release-signer",
            "KMH_OIA_ATTESTATION_ALLOWED_SUBJECTS": "repo:thuyainminnyo-hub/kmh-oia:ref:refs/heads/main",
            "KMH_OIA_ATTESTATION_EXPECTED_SOURCE_REVISION": self.source_revision,
            "KMH_OIA_ATTESTATION_MAX_AGE_SECONDS": "1800",
            "KMH_OIA_ATTESTATION_MAX_CLOCK_SKEW_SECONDS": "60",
        }
        self.attestation = RuntimeArtifactAttestation(
            classifier_sha256=hashlib.sha256(self.classifier_bytes).hexdigest(),
            policy_sha256=hashlib.sha256(self.policy_bytes).hexdigest(),
            issuer="kmh-release-signer",
            subject="repo:thuyainminnyo-hub/kmh-oia:ref:refs/heads/main",
            attestation_id="release-attestation-806",
            key_id="prod-signing-key-2026",
            source_revision=self.source_revision,
            build_run_id="release-run-20261021",
            issued_at=self.now.isoformat().replace("+00:00", "Z"),
        )
        self.attestation = replace(self.attestation, signature=base64.b64encode(
            self.private_key.sign(canonical_attestation_payload(self.attestation))
        ).decode("ascii"))

    def test_valid_production_config_parses(self):
        config = load_production_artifact_trust_config(self.env)
        self.assertEqual(config.expected_source_revision, self.source_revision)
        self.assertEqual(config.max_age_seconds, 1800)
        self.assertEqual(config.max_clock_skew_seconds, 60)
        self.assertEqual(config.allowed_issuers, ("kmh-release-signer",))

    def test_production_loader_verifies_signer_revision_and_bytes_before_load(self):
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            classifier_path = Path(directory) / "classifier.bin"
            policy_path = Path(directory) / "policy.bin"
            classifier_path.write_bytes(self.classifier_bytes)
            policy_path.write_bytes(self.policy_bytes)
            bundle = load_production_runtime_artifacts(
                classifier_path, policy_path, attestation=self.attestation, environ=self.env,
                classifier_loader=lambda payload: calls.append(("classifier", payload)) or payload,
                policy_loader=lambda payload: calls.append(("policy", payload)) or payload,
            )
        self.assertEqual(bundle.classifier, self.classifier_bytes)
        self.assertEqual(bundle.policy, self.policy_bytes)
        self.assertEqual([item[0] for item in calls], ["classifier", "policy"])
        self.assertTrue(bundle.verify_integrity())

    def test_missing_production_environment_fails_closed(self):
        env = dict(self.env)
        env.pop("KMH_OIA_ENVIRONMENT")
        with self.assertRaisesRegex(ProductionArtifactTrustConfigError, "explicitly set to production"):
            load_production_artifact_trust_config(env)

    def test_missing_trust_key_fails_closed(self):
        env = dict(self.env)
        env.pop("KMH_OIA_ATTESTATION_TRUSTED_PUBLIC_KEYS_JSON")
        with self.assertRaisesRegex(ProductionArtifactTrustConfigError, "TRUSTED_PUBLIC_KEYS_JSON is required"):
            load_production_artifact_trust_config(env)

    def test_malformed_or_wrong_length_public_key_fails_closed(self):
        env = dict(self.env)
        env["KMH_OIA_ATTESTATION_TRUSTED_PUBLIC_KEYS_JSON"] = json.dumps({"prod-signing-key-2026": base64.b64encode(b"short").decode("ascii")})
        with self.assertRaisesRegex(ProductionArtifactTrustConfigError, "32 raw Ed25519 bytes"):
            load_production_artifact_trust_config(env)

    def test_placeholder_issuer_and_wildcard_allowlist_are_rejected(self):
        env = dict(self.env)
        env["KMH_OIA_ATTESTATION_ALLOWED_ISSUERS"] = "test-ci"
        with self.assertRaisesRegex(ProductionArtifactTrustConfigError, "placeholder identity"):
            load_production_artifact_trust_config(env)
        env = dict(self.env)
        env["KMH_OIA_ATTESTATION_ALLOWED_SUBJECTS"] = "*"
        with self.assertRaisesRegex(ProductionArtifactTrustConfigError, "non-wildcard allowlist"):
            load_production_artifact_trust_config(env)

    def test_invalid_age_skew_and_revision_pins_are_rejected(self):
        env = dict(self.env)
        env["KMH_OIA_ATTESTATION_MAX_AGE_SECONDS"] = "0"
        with self.assertRaisesRegex(ProductionArtifactTrustConfigError, "must be greater than zero"):
            load_production_artifact_trust_config(env)
        env = dict(self.env)
        env["KMH_OIA_ATTESTATION_MAX_CLOCK_SKEW_SECONDS"] = "0"
        with self.assertRaises(ProductionArtifactTrustConfigError):
            load_production_artifact_trust_config(env)
        env = dict(self.env)
        env["KMH_OIA_ATTESTATION_EXPECTED_SOURCE_REVISION"] = "short"
        with self.assertRaisesRegex(ProductionArtifactTrustConfigError, "full 40- or 64-character"):
            load_production_artifact_trust_config(env)

    def test_source_revision_mismatch_blocks_loaders(self):
        env = dict(self.env)
        env["KMH_OIA_ATTESTATION_EXPECTED_SOURCE_REVISION"] = "e" * 40
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            classifier_path = Path(directory) / "classifier.bin"
            policy_path = Path(directory) / "policy.bin"
            classifier_path.write_bytes(self.classifier_bytes)
            policy_path.write_bytes(self.policy_bytes)
            with self.assertRaisesRegex(ProductionArtifactTrustConfigError, "source revision does not match"):
                load_production_runtime_artifacts(
                    classifier_path, policy_path, attestation=self.attestation, environ=env,
                    classifier_loader=lambda payload: calls.append("classifier"),
                    policy_loader=lambda payload: calls.append("policy"),
                )
        self.assertEqual(calls, [])

    def test_tampered_file_blocks_production_loader(self):
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            classifier_path = Path(directory) / "classifier.bin"
            policy_path = Path(directory) / "policy.bin"
            classifier_path.write_bytes(self.classifier_bytes + b"tampered")
            policy_path.write_bytes(self.policy_bytes)
            with self.assertRaisesRegex(ProductionArtifactTrustConfigError, "failed closed"):
                load_production_runtime_artifacts(
                    classifier_path, policy_path, attestation=self.attestation, environ=self.env,
                    classifier_loader=lambda payload: calls.append("classifier"),
                    policy_loader=lambda payload: calls.append("policy"),
                )
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
