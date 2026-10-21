import base64
import hashlib
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from scripts.create_runtime_bundle_attestation import (
    RuntimeBundleAttestationCreationError, create_signed_runtime_bundle_attestation,
)
from scripts.package_runtime_bundle import build_runtime_bundle
from scripts.validate_runtime_bundle import validate_runtime_bundle
from src.runtime_bundle_attestation import (
    Ed25519RuntimeBundleAttestationVerifier, RuntimeBundleAttestation, canonical_runtime_bundle_payload,
)
from src.runtime_bundle_attestation_io import (
    RuntimeBundleAttestationIOError, load_runtime_bundle_attestation, write_runtime_bundle_attestation,
)

class RuntimeBundleAttestationTests(unittest.TestCase):
    def setUp(self):
        self.private_key = Ed25519PrivateKey.generate()
        self.private_raw = self.private_key.private_bytes_raw()
        self.public_key = self.private_key.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
        self.now = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
        self.verifier = Ed25519RuntimeBundleAttestationVerifier(
            {'bundle-key': self.public_key}, allowed_issuers=('kmh-release-signer',),
            allowed_subjects=('repo:thuyainminnyo-hub/kmh-oia:ref:refs/heads/main',),
            max_age_seconds=3600, max_clock_skew_seconds=60, clock=lambda: self.now,
        )
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'src').mkdir()
        (self.root / 'src' / 'runtime.py').write_text('VALUE = 1\n', encoding='utf-8')
        (self.root / 'requirements.txt').write_text('cryptography==50.0.2\n', encoding='utf-8')
        self.revision = 'a' * 40
        self.bundle = self.root / 'runtime-source-bundle.tar.gz'
        build_runtime_bundle(self.root, self.revision, self.bundle)
        self.digest = hashlib.sha256(self.bundle.read_bytes()).hexdigest()
        self.env = {
            'KMH_OIA_ATTESTATION_PRIVATE_KEY_B64': base64.b64encode(self.private_raw).decode('ascii'),
            'KMH_OIA_ATTESTATION_KEY_ID': 'bundle-key', 'KMH_OIA_ATTESTATION_ISSUER': 'kmh-release-signer',
            'KMH_OIA_ATTESTATION_SUBJECT': 'repo:thuyainminnyo-hub/kmh-oia:ref:refs/heads/main',
            'KMH_OIA_ENVIRONMENT': 'production', 'GITHUB_ACTIONS': 'true', 'GITHUB_REF': 'refs/heads/main',
            'GITHUB_EVENT_NAME': 'workflow_dispatch', 'GITHUB_SHA': self.revision, 'GITHUB_RUN_ID': '12345',
        }

    def create(self, **overrides):
        return create_signed_runtime_bundle_attestation(
            self.bundle, source_revision=self.revision, build_run_id='12345', artifact_id='67890',
            artifact_name='kmh-oia-runtime-bundle', artifact_digest='sha256:' + 'b' * 64,
            environ={**self.env, **overrides},
        )

    def test_sign_write_load_and_verify_real_bundle_bytes(self):
        attestation = self.create()
        path = self.root / 'attestation.json'
        write_runtime_bundle_attestation(path, attestation)
        parsed = load_runtime_bundle_attestation(path)
        self.assertTrue(self.verifier.verify(
            parsed, expected_bundle_sha256=self.digest, expected_source_revision=self.revision,
            expected_build_run_id='12345', expected_artifact_id='67890',
            expected_artifact_name='kmh-oia-runtime-bundle', expected_artifact_digest='sha256:' + 'b' * 64,
        ))
        self.assertEqual(parsed.bundle_sha256, self.digest)

    def test_changed_bundle_digest_source_sha_or_artifact_metadata_is_rejected(self):
        attestation = self.create()
        expected = dict(expected_bundle_sha256=self.digest, expected_source_revision=self.revision,
                        expected_build_run_id='12345', expected_artifact_id='67890',
                        expected_artifact_name='kmh-oia-runtime-bundle', expected_artifact_digest='sha256:' + 'b' * 64)
        self.assertFalse(self.verifier.verify(attestation, **{**expected, 'expected_bundle_sha256': 'f' * 64}))
        self.assertFalse(self.verifier.verify(attestation, **{**expected, 'expected_artifact_id': '99999'}))
        self.assertFalse(self.verifier.verify(attestation, **{**expected, 'expected_source_revision': 'c' * 40}))
        tampered = replace(attestation, source_revision='c' * 40)
        self.assertFalse(self.verifier.verify(tampered, **expected))

    def test_production_context_mismatch_and_missing_key_fail_closed(self):
        with self.assertRaisesRegex(RuntimeBundleAttestationCreationError, 'must match trusted GITHUB_SHA'):
            self.create(GITHUB_SHA='c' * 40)
        env = dict(self.env)
        env.pop('KMH_OIA_ATTESTATION_PRIVATE_KEY_B64')
        with self.assertRaisesRegex(RuntimeBundleAttestationCreationError, 'is required'):
            create_signed_runtime_bundle_attestation(
                self.bundle, source_revision=self.revision, build_run_id='12345', artifact_id='67890',
                artifact_name='kmh-oia-runtime-bundle', artifact_digest='sha256:' + 'b' * 64, environ=env,
            )

    def test_writer_is_create_only_and_reader_rejects_extra_fields(self):
        attestation = self.create()
        path = self.root / 'attestation.json'
        write_runtime_bundle_attestation(path, attestation)
        with self.assertRaisesRegex(RuntimeBundleAttestationIOError, 'refusing to overwrite'):
            write_runtime_bundle_attestation(path, attestation)
        data = path.read_text(encoding='utf-8')
        path.write_text(data.replace('\\n}', ',"unexpected":"field"\\n}'), encoding='utf-8')
        with self.assertRaisesRegex(RuntimeBundleAttestationIOError, 'exactly the supported fields'):
            load_runtime_bundle_attestation(path)

if __name__ == '__main__':
    unittest.main()
