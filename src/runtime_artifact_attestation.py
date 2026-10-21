"""Cryptographic Ed25519 verification for runtime artifact provenance.

Public keys must be supplied from a trusted configuration/secret-management path.
The signed canonical payload binds artifact digests to issuer, subject, build run,
source revision, key id, and issuance time. This is a verifier, not a build signer.
"""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Mapping, Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from src.runtime_artifact_measurement import normalize_sha256


@dataclass(frozen=True)
class RuntimeArtifactAttestation:
    """Signed identity statement binding exact artifacts to build provenance."""
    classifier_sha256: str
    policy_sha256: str
    issuer: str
    subject: str
    attestation_id: str
    key_id: str = ""
    source_revision: str = ""
    build_run_id: str = ""
    issued_at: str = ""
    signature: str = ""
    schema_version: int = 1


class RuntimeArtifactAttestationVerifier(Protocol):
    def verify(
        self, attestation: RuntimeArtifactAttestation, *,
        expected_classifier_sha256: str, expected_policy_sha256: str,
    ) -> bool: ...


def canonical_attestation_payload(attestation: RuntimeArtifactAttestation) -> bytes:
    """Canonical UTF-8 JSON bytes covered by the Ed25519 signature."""
    statement = {
        "schema_version": attestation.schema_version,
        "key_id": attestation.key_id,
        "issuer": attestation.issuer,
        "subject": attestation.subject,
        "attestation_id": attestation.attestation_id,
        "source_revision": attestation.source_revision,
        "build_run_id": attestation.build_run_id,
        "issued_at": attestation.issued_at,
        "classifier_sha256": normalize_sha256(attestation.classifier_sha256),
        "policy_sha256": normalize_sha256(attestation.policy_sha256),
    }
    return json.dumps(statement, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


class Ed25519RuntimeArtifactAttestationVerifier:
    """Fail-closed Ed25519 verifier using explicitly trusted public keys."""

    def __init__(
        self,
        trusted_public_keys: Mapping[str, bytes],
        *,
        allowed_issuers: tuple[str, ...],
        allowed_subjects: tuple[str, ...],
        max_age_seconds: int | None = None,
        max_clock_skew_seconds: int = 300,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not trusted_public_keys:
            raise ValueError("at least one trusted Ed25519 public key is required")
        if not allowed_issuers or any(not isinstance(x, str) or not x.strip() for x in allowed_issuers):
            raise ValueError("allowed_issuers must contain non-empty issuer names")
        if not allowed_subjects or any(not isinstance(x, str) or not x.strip() for x in allowed_subjects):
            raise ValueError("allowed_subjects must contain non-empty subjects")
        if max_age_seconds is not None and max_age_seconds <= 0:
            raise ValueError("max_age_seconds must be positive when configured")
        if max_clock_skew_seconds < 0:
            raise ValueError("max_clock_skew_seconds cannot be negative")
        normalized: dict[str, bytes] = {}
        for key_id, raw_key in trusted_public_keys.items():
            if not isinstance(key_id, str) or not key_id.strip():
                raise ValueError("trusted key identifiers must be non-empty strings")
            if not isinstance(raw_key, bytes) or len(raw_key) != 32:
                raise ValueError(f"trusted Ed25519 public key {key_id!r} must be exactly 32 raw bytes")
            normalized[key_id] = bytes(raw_key)
        self._trusted_public_keys = normalized
        self._allowed_issuers = frozenset(allowed_issuers)
        self._allowed_subjects = frozenset(allowed_subjects)
        self._max_age_seconds = max_age_seconds
        self._max_clock_skew_seconds = max_clock_skew_seconds
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def verify(
        self, attestation: RuntimeArtifactAttestation, *,
        expected_classifier_sha256: str, expected_policy_sha256: str,
    ) -> bool:
        """Authenticate a statement, allowlisted issuer/subject, and pinned digests."""
        try:
            if not isinstance(attestation, RuntimeArtifactAttestation):
                return False
            if attestation.schema_version != 1:
                return False
            if not attestation.key_id or attestation.key_id not in self._trusted_public_keys:
                return False
            if attestation.issuer not in self._allowed_issuers or attestation.subject not in self._allowed_subjects:
                return False
            for value in (attestation.attestation_id, attestation.source_revision, attestation.build_run_id, attestation.issued_at, attestation.signature):
                if not isinstance(value, str) or not value.strip():
                    return False
            if len(attestation.source_revision) not in (40, 64) or any(c not in "0123456789abcdefABCDEF" for c in attestation.source_revision):
                return False
            if normalize_sha256(attestation.classifier_sha256) != normalize_sha256(expected_classifier_sha256):
                return False
            if normalize_sha256(attestation.policy_sha256) != normalize_sha256(expected_policy_sha256):
                return False
            issued_at = datetime.fromisoformat(attestation.issued_at.replace("Z", "+00:00"))
            if issued_at.tzinfo is None or issued_at.utcoffset() is None:
                return False
            now = self._clock()
            if now.tzinfo is None or now.utcoffset() is None:
                return False
            age_seconds = (now - issued_at.astimezone(timezone.utc)).total_seconds()
            if age_seconds < -self._max_clock_skew_seconds:
                return False
            if self._max_age_seconds is not None and age_seconds > self._max_age_seconds:
                return False
            signature = base64.b64decode(attestation.signature, validate=True)
            Ed25519PublicKey.from_public_bytes(self._trusted_public_keys[attestation.key_id]).verify(
                signature, canonical_attestation_payload(attestation)
            )
            return True
        except (InvalidSignature, ValueError, TypeError, KeyError, OverflowError):
            return False

