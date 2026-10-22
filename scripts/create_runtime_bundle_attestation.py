"""Create an Ed25519 attestation for a validated runtime-source bundle."""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import sys
from typing import Mapping

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from src.runtime_bundle_attestation import RuntimeBundleAttestation, canonical_runtime_bundle_payload
from src.runtime_bundle_attestation_io import RuntimeBundleAttestationIOError, write_runtime_bundle_attestation
from scripts.validate_runtime_bundle import validate_runtime_bundle


class RuntimeBundleAttestationCreationError(ValueError):
    pass

def create_signed_runtime_bundle_attestation(
    bundle_path: str | Path, *, source_revision: str, build_run_id: str,
    artifact_id: str, artifact_name: str, artifact_digest: str,
    environ: Mapping[str, str] | None = None,
) -> RuntimeBundleAttestation:
    env = os.environ if environ is None else environ
    raw_key = env.get('KMH_OIA_ATTESTATION_PRIVATE_KEY_B64')
    if not isinstance(raw_key, str) or not raw_key.strip():
        raise RuntimeBundleAttestationCreationError('KMH_OIA_ATTESTATION_PRIVATE_KEY_B64 is required')
    try:
        key_bytes = base64.b64decode(raw_key, validate=True)
    except (ValueError, TypeError) as exc:
        raise RuntimeBundleAttestationCreationError('signing key must be valid base64') from exc
    if len(key_bytes) != 32:
        raise RuntimeBundleAttestationCreationError('signing key must decode to 32 raw Ed25519 seed bytes')
    try:
        private_key = Ed25519PrivateKey.from_private_bytes(key_bytes)
    except ValueError as exc:
        raise RuntimeBundleAttestationCreationError('Ed25519 signing key is invalid') from exc
    key_id = env.get('KMH_OIA_ATTESTATION_KEY_ID', '').strip()
    issuer = env.get('KMH_OIA_ATTESTATION_ISSUER', '').strip()
    subject = env.get('KMH_OIA_ATTESTATION_SUBJECT', '').strip()
    if any(not item or item == '*' for item in (key_id, issuer, subject)):
        raise RuntimeBundleAttestationCreationError('key ID, issuer and exact subject are required')
    revision = source_revision.strip().lower() if isinstance(source_revision, str) else ''
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise RuntimeBundleAttestationCreationError('source_revision must be a full lowercase 40-character SHA')
    for name, value in (('build_run_id', build_run_id), ('artifact_id', artifact_id)):
        if not isinstance(value, str) or not value.isdigit() or value.startswith('0'):
            raise RuntimeBundleAttestationCreationError(f'{name} must be a canonical positive decimal ID')
    if not isinstance(artifact_name, str) or artifact_name != 'kmh-oia-runtime-bundle':
        raise RuntimeBundleAttestationCreationError('artifact_name must match the exact approved runtime bundle name')
    if not isinstance(artifact_digest, str) or not re.fullmatch(r'sha256:[0-9a-f]{64}', artifact_digest):
        raise RuntimeBundleAttestationCreationError('artifact_digest must use sha256:<64 lowercase hex>')
    try:
        measurement = validate_runtime_bundle(bundle_path, expected_source_sha=revision)
    except (ValueError, OSError) as exc:
        raise RuntimeBundleAttestationCreationError(f'runtime bundle validation failed: {exc}') from exc
    if env.get('KMH_OIA_ENVIRONMENT', '').strip().casefold() == 'production':
        if env.get('GITHUB_ACTIONS', '').strip().lower() != 'true':
            raise RuntimeBundleAttestationCreationError('production signing requires the GitHub Actions runtime context')
        if env.get('GITHUB_SHA', '').strip().lower() != revision:
            raise RuntimeBundleAttestationCreationError('source_revision must match trusted GITHUB_SHA')
        if env.get('GITHUB_RUN_ID', '').strip() != build_run_id:
            raise RuntimeBundleAttestationCreationError('build_run_id must match trusted GITHUB_RUN_ID')
        if env.get('GITHUB_REF', '').strip() != 'refs/heads/main':
            raise RuntimeBundleAttestationCreationError('production signing is allowed only from refs/heads/main')
        if env.get('GITHUB_EVENT_NAME', '').strip() != 'workflow_dispatch':
            raise RuntimeBundleAttestationCreationError('production signing requires a workflow_dispatch event')
    statement = RuntimeBundleAttestation(
        bundle_sha256=measurement['bundle_sha256'], issuer=issuer, subject=subject,
        attestation_id=f'{key_id}:{build_run_id}', key_id=key_id,
        source_revision=revision, build_run_id=build_run_id, artifact_id=artifact_id,
        artifact_name=artifact_name, artifact_digest=artifact_digest,
        issued_at=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    )
    signature = private_key.sign(canonical_runtime_bundle_payload(statement))
    return RuntimeBundleAttestation(**{**statement.__dict__, 'signature': base64.b64encode(signature).decode('ascii')})

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--source-revision', required=True)
    parser.add_argument('--build-run-id', required=True)
    parser.add_argument('--artifact-id', required=True)
    parser.add_argument('--artifact-name', required=True)
    parser.add_argument('--artifact-digest', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    try:
        attestation = create_signed_runtime_bundle_attestation(
            args.bundle, source_revision=args.source_revision, build_run_id=args.build_run_id,
            artifact_id=args.artifact_id, artifact_name=args.artifact_name, artifact_digest=args.artifact_digest,
        )
        write_runtime_bundle_attestation(args.output, attestation)
    except (RuntimeBundleAttestationCreationError, RuntimeBundleAttestationIOError) as exc:
        print(f'runtime bundle attestation creation failed closed: {exc}', file=sys.stderr)
        return 2
    print('signed runtime bundle attestation created: id=' + attestation.attestation_id)
    print('bundle_sha256=' + attestation.bundle_sha256)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
