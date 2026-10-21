import base64
import hashlib
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from scripts.create_runtime_artifact_attestation import (
    RuntimeArtifactAttestationCreationError, create_signed_runtime_attestation,
)
from src.runtime_artifact_attestation import Ed25519RuntimeArtifactAttestationVerifier
from src.runtime_artifact_io import (
    RuntimeArtifactAttestationIOError, load_runtime_artifact_attestation,
    write_runtime_artifact_attestation,
)


class RuntimeArtifactAttestationProducerTests(unittest.TestCase):
    def setUp(self):
        self.private_key = Ed25519PrivateKey.generate()
        private_bytes = self.private_key.private_bytes_raw()
        self.public_key = self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw,
        )
        self.env = {
            "KMH_OIA_ATTESTATION_PRIVATE_KEY_B64": base64.b64encode(private_bytes).decode("ascii"),
            "KMH_OIA_ATTESTATION_KEY_ID": "release-key-808",
            "KMH_OIA_ATTESTATION_ISSUER": "kmh-release-signer",
            "KMH_OIA_ATTESTATION_SUBJECT": "repo:thuyainminnyo-hub/kmh-oia:ref:refs/heads/main",
            "KMH_OIA_ENVIRONMENT": "production",
            "GITHUB_ACTIONS": "true",
            "GITHUB_REF": "refs/heads/main",
            "GITHUB_EVENT_NAME": "workflow_dispatch",
        }
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.classifier_path = Path(self.temp.name) / "classifier.bin"
        self.policy_path = Path(self.temp.name) / "policy.bin"
        self.output_path = Path(self.temp.name) / "attestation.json"
        self.classifier_bytes = b"classifier-v808-bytes"
        self.policy_bytes = b"policy-v808-bytes"
        self.classifier_path.write_bytes(self.classifier_bytes)
        self.policy_path.write_bytes(self.policy_bytes)
        self.revision = "a" * 40
        self.env.update({"GITHUB_SHA": self.revision, "GITHUB_RUN_ID": "run-808-1"})

    def test_sign_and_parse_attestation_verifies_against_measured_bytes(self):
        attestation = create_signed_runtime_attestation(
            self.classifier_path, self.policy_path,
            source_revision=self.revision, build_run_id="run-808-1", environ=self.env,
        )
        write_runtime_artifact_attestation(self.output_path, attestation)
        parsed = load_runtime_artifact_attestation(self.output_path)
        verifier = Ed25519RuntimeArtifactAttestationVerifier(
            {"release-key-808": self.public_key},
            allowed_issuers=("kmh-release-signer",),
            allowed_subjects=("repo:thuyainminnyo-hub/kmh-oia:ref:refs/heads/main",),
            max_age_seconds=3600, max_clock_skew_seconds=60,
        )
        self.assertTrue(verifier.verify(
            parsed,
            expected_classifier_sha256=hashlib.sha256(self.classifier_bytes).hexdigest(),
            expected_policy_sha256=hashlib.sha256(self.policy_bytes).hexdigest(),
        ))
        self.assertEqual(parsed.source_revision, self.revision)
        self.assertEqual(parsed.classifier_sha256, hashlib.sha256(self.classifier_bytes).hexdigest())

    def test_changed_artifact_bytes_do_not_match_signed_statement(self):
        attestation = create_signed_runtime_attestation(
            self.classifier_path, self.policy_path,
            source_revision=self.revision, build_run_id="run-808-2", environ={**self.env, "GITHUB_RUN_ID": "run-808-2"},
        )
        self.classifier_path.write_bytes(b"tampered after signing")
        verifier = Ed25519RuntimeArtifactAttestationVerifier(
            {"release-key-808": self.public_key},
            allowed_issuers=("kmh-release-signer",),
            allowed_subjects=("repo:thuyainminnyo-hub/kmh-oia:ref:refs/heads/main",),
            max_age_seconds=3600, max_clock_skew_seconds=60,
        )
        self.assertFalse(verifier.verify(
            attestation,
            expected_classifier_sha256=hashlib.sha256(self.classifier_path.read_bytes()).hexdigest(),
            expected_policy_sha256=hashlib.sha256(self.policy_bytes).hexdigest(),
        ))

    def test_missing_or_malformed_signing_key_fails_closed(self):
        env = dict(self.env)
        env.pop("KMH_OIA_ATTESTATION_PRIVATE_KEY_B64")
        with self.assertRaisesRegex(RuntimeArtifactAttestationCreationError, "is required"):
            create_signed_runtime_attestation(self.classifier_path, self.policy_path, source_revision=self.revision, build_run_id="run", environ=env)
        env = dict(self.env)
        env["KMH_OIA_ATTESTATION_PRIVATE_KEY_B64"] = "not-base64***"
        with self.assertRaisesRegex(RuntimeArtifactAttestationCreationError, "valid base64"):
            create_signed_runtime_attestation(self.classifier_path, self.policy_path, source_revision=self.revision, build_run_id="run", environ=env)

    def test_bad_revision_metadata_and_empty_artifacts_fail_closed(self):
        with self.assertRaisesRegex(RuntimeArtifactAttestationCreationError, "full 40- or 64-character"):
            create_signed_runtime_attestation(self.classifier_path, self.policy_path, source_revision="bad", build_run_id="run", environ=self.env)
        env = dict(self.env)
        env["KMH_OIA_ATTESTATION_SUBJECT"] = "*"
        with self.assertRaisesRegex(RuntimeArtifactAttestationCreationError, "exact subject"):
            create_signed_runtime_attestation(self.classifier_path, self.policy_path, source_revision=self.revision, build_run_id="run", environ=env)
        self.policy_path.write_bytes(b"")
        with self.assertRaisesRegex(RuntimeArtifactAttestationCreationError, "must not be empty"):
            create_signed_runtime_attestation(self.classifier_path, self.policy_path, source_revision=self.revision, build_run_id="run", environ=self.env)

    def test_production_signer_requires_sha_and_run_id_to_match_github_context(self):
        env = dict(self.env)
        env["GITHUB_SHA"] = "b" * 40
        with self.assertRaisesRegex(RuntimeArtifactAttestationCreationError, "must match the trusted GITHUB_SHA"):
            create_signed_runtime_attestation(
                self.classifier_path, self.policy_path, source_revision=self.revision,
                build_run_id="run-808-1", environ=env,
            )
        env = dict(self.env)
        env["GITHUB_RUN_ID"] = "other-run"
        with self.assertRaisesRegex(RuntimeArtifactAttestationCreationError, "must match the trusted GITHUB_RUN_ID"):
            create_signed_runtime_attestation(
                self.classifier_path, self.policy_path, source_revision=self.revision,
                build_run_id="run-808-1", environ=env,
            )

    def test_production_signer_rejects_missing_actions_context_branch_and_event(self):
        env = dict(self.env)
        env.pop("GITHUB_ACTIONS")
        with self.assertRaisesRegex(RuntimeArtifactAttestationCreationError, "requires the GitHub Actions runtime context"):
            create_signed_runtime_attestation(
                self.classifier_path, self.policy_path, source_revision=self.revision,
                build_run_id="run-808-1", environ=env,
            )
        env = dict(self.env)
        env["GITHUB_REF"] = "refs/heads/feature"
        with self.assertRaisesRegex(RuntimeArtifactAttestationCreationError, "only from refs/heads/main"):
            create_signed_runtime_attestation(
                self.classifier_path, self.policy_path, source_revision=self.revision,
                build_run_id="run-808-1", environ=env,
            )
        env = dict(self.env)
        env["GITHUB_EVENT_NAME"] = "pull_request"
        with self.assertRaisesRegex(RuntimeArtifactAttestationCreationError, "requires a workflow_dispatch"):
            create_signed_runtime_attestation(
                self.classifier_path, self.policy_path, source_revision=self.revision,
                build_run_id="run-808-1", environ=env,
            )

    def test_writer_refuses_overwrite_and_reader_rejects_extra_fields(self):
        attestation = create_signed_runtime_attestation(
            self.classifier_path, self.policy_path,
            source_revision=self.revision, build_run_id="run-808-3", environ={**self.env, "GITHUB_RUN_ID": "run-808-3"},
        )
        write_runtime_artifact_attestation(self.output_path, attestation)
        with self.assertRaisesRegex(RuntimeArtifactAttestationIOError, "refusing to overwrite"):
            write_runtime_artifact_attestation(self.output_path, attestation)
        self.output_path.write_text(self.output_path.read_text()[:-2] + ', "unexpected":"field"}\n', encoding="utf-8")
        with self.assertRaisesRegex(RuntimeArtifactAttestationIOError, "exactly the supported fields"):
            load_runtime_artifact_attestation(self.output_path)


if __name__ == "__main__":
    unittest.main()
