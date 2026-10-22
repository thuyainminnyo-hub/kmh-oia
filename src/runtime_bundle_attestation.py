"""Ed25519 attestations for the actual KMH OIA runtime source bundle."""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from src.runtime_artifact_measurement import normalize_sha256


@dataclass(frozen=True)
class RuntimeBundleAttestation:
    bundle_sha256: str
    issuer: str
    subject: str
    attestation_id: str
    key_id: str
    source_revision: str
    build_run_id: str
    artifact_id: str
    artifact_name: str
    artifact_digest: str
    issued_at: str
    signature: str = ''
    schema_version: int = 1


def canonical_runtime_bundle_payload(attestation: RuntimeBundleAttestation) -> bytes:
    statement = {
        'schema_version': attestation.schema_version,
        'key_id': attestation.key_id,
        'issuer': attestation.issuer,
        'subject': attestation.subject,
        'attestation_id': attestation.attestation_id,
        'source_revision': attestation.source_revision.lower(),
        'build_run_id': attestation.build_run_id,
        'artifact_id': attestation.artifact_id,
        'artifact_name': attestation.artifact_name,
        'artifact_digest': 'sha256:' + normalize_sha256(attestation.artifact_digest),
        'bundle_sha256': normalize_sha256(attestation.bundle_sha256),
        'issued_at': attestation.issued_at,
    }
    return json.dumps(statement, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


class Ed25519RuntimeBundleAttestationVerifier:
    def __init__(
        self, trusted_public_keys: Mapping[str, bytes], *,
        allowed_issuers: tuple[str, ...], allowed_subjects: tuple[str, ...],
        max_age_seconds: int | None = None, max_clock_skew_seconds: int = 300,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not trusted_public_keys:
            raise ValueError('at least one trusted Ed25519 public key is required')
        if not allowed_issuers or any(not isinstance(v, str) or not v.strip() for v in allowed_issuers):
            raise ValueError('allowed_issuers must contain non-empty names')
        if not allowed_subjects or any(not isinstance(v, str) or not v.strip() for v in allowed_subjects):
            raise ValueError('allowed_subjects must contain non-empty subjects')
        if max_age_seconds is not None and (isinstance(max_age_seconds, bool) or max_age_seconds <= 0):
            raise ValueError('max_age_seconds must be positive when configured')
        if isinstance(max_clock_skew_seconds, bool) or max_clock_skew_seconds < 0:
            raise ValueError('max_clock_skew_seconds cannot be negative')
        self._keys = {}
        for key_id, raw in trusted_public_keys.items():
            if not isinstance(key_id, str) or not key_id.strip() or not isinstance(raw, bytes) or len(raw) != 32:
                raise ValueError('each trusted key needs a non-empty ID and exactly 32 raw Ed25519 bytes')
            self._keys[key_id] = bytes(raw)
        self._issuers = frozenset(allowed_issuers)
        self._subjects = frozenset(allowed_subjects)
        self._max_age = max_age_seconds
        self._skew = max_clock_skew_seconds
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def verify(
        self, attestation: RuntimeBundleAttestation, *,
        expected_bundle_sha256: str, expected_source_revision: str,
        expected_build_run_id: str, expected_artifact_id: str,
        expected_artifact_name: str, expected_artifact_digest: str,
    ) -> bool:
        try:
            if not isinstance(attestation, RuntimeBundleAttestation) or attestation.schema_version != 1:
                return False
            if not attestation.key_id or attestation.key_id not in self._keys:
                return False
            if attestation.issuer not in self._issuers or attestation.subject not in self._subjects:
                return False
            strings = (attestation.attestation_id, attestation.source_revision, attestation.build_run_id,
                       attestation.artifact_id, attestation.artifact_name, attestation.artifact_digest,
                       attestation.issued_at, attestation.signature)
            if any(not isinstance(v, str) or not v.strip() for v in strings):
                return False
            rev = attestation.source_revision.lower()
            if len(rev) not in (40, 64) or any(c not in '0123456789abcdef' for c in rev):
                return False
            if rev != expected_source_revision.lower():
                return False
            for value in (attestation.build_run_id, attestation.artifact_id):
                if not value.isdigit() or value.startswith('0'):
                    return False
            if attestation.build_run_id != expected_build_run_id or attestation.artifact_id != expected_artifact_id:
                return False
            if attestation.artifact_name != expected_artifact_name:
                return False
            if normalize_sha256(attestation.bundle_sha256) != normalize_sha256(expected_bundle_sha256):
                return False
            if normalize_sha256(attestation.artifact_digest) != normalize_sha256(expected_artifact_digest):
                return False
            issued = datetime.fromisoformat(attestation.issued_at.replace('Z', '+00:00'))
            now = self._clock()
            if issued.tzinfo is None or issued.utcoffset() is None or now.tzinfo is None or now.utcoffset() is None:
                return False
            age = (now.astimezone(timezone.utc) - issued.astimezone(timezone.utc)).total_seconds()
            if age < -self._skew or (self._max_age is not None and age > self._max_age):
                return False
            signature = base64.b64decode(attestation.signature, validate=True)
            Ed25519PublicKey.from_public_bytes(self._keys[attestation.key_id]).verify(
                signature, canonical_runtime_bundle_payload(attestation)
            )
            return True
        except (InvalidSignature, ValueError, TypeError, KeyError, OverflowError):
            return False
