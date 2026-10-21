"""Fail-closed production trust-root configuration for signed runtime artifacts."""
from __future__ import annotations

from dataclasses import dataclass
import base64
import json
import os
from typing import Mapping

from src.runtime_artifact_attestation import Ed25519RuntimeArtifactAttestationVerifier, RuntimeArtifactAttestation
from src.runtime_artifact_loader import VerifiedRuntimeArtifacts, verify_and_load_runtime_artifacts


class ProductionArtifactTrustConfigError(ValueError):
    """Raised when required production trust configuration is missing or unsafe."""


@dataclass(frozen=True)
class ProductionArtifactTrustConfig:
    trusted_public_keys: dict[str, bytes]
    allowed_issuers: tuple[str, ...]
    allowed_subjects: tuple[str, ...]
    expected_source_revision: str
    max_age_seconds: int
    max_clock_skew_seconds: int

    def create_verifier(self) -> Ed25519RuntimeArtifactAttestationVerifier:
        return Ed25519RuntimeArtifactAttestationVerifier(
            self.trusted_public_keys,
            allowed_issuers=self.allowed_issuers,
            allowed_subjects=self.allowed_subjects,
            max_age_seconds=self.max_age_seconds,
            max_clock_skew_seconds=self.max_clock_skew_seconds,
        )


_PLACEHOLDER_IDENTITIES = frozenset({
    "test-ci", "test", "fake", "placeholder", "unit-test", "unit-test-runtime",
    "test-loaded-runtime", "test-key-1", "test-key-2",
})


def _csv_allowlist(value: str | None, *, name: str) -> tuple[str, ...]:
    if not isinstance(value, str) or not value.strip():
        raise ProductionArtifactTrustConfigError(f"{name} is required")
    items = tuple(part.strip() for part in value.split(",") if part.strip())
    if not items or len(set(items) != len(items) or "*" in items:
        raise ProductionArtifactTrustConfigError(f"{name} must be an explicit, unique, non-wildcard allowlist")
    if any(item.casefold() in _PLACEHOLDER_IDENTITIES for item in items):
        raise ProductionArtifactTrustConfigError(f"{name} contains a test or placeholder identity")
    return items


def load_production_artifact_trust_config(
    environ: Mapping[str, str] | None = None,
) -> ProductionArtifactTrustConfig:
    """Parse mandatory production trust anchors and release pins, failing closed."""
    env = os.environ if environ is None else environ
    if env.get("KMH_OIA_ENVIRONMENT", "").strip().casefold() != "production":
        raise ProductionArtifactTrustConfigError("KMH_OIA_ENVIRONMENT must be explicitly set to production")

    keys_json = env.get("KMH_OIA_ATTESTATION_TRUSTED_PUBLIC_KEYS_JSON")
    if not isinstance(keys_json, str) or not keys_json.strip():
        raise ProductionArtifactTrustConfigError("KMH_OIA_ATTESTATION_TRUSTED_PUBLIC_KEYS_JSON is required")
    if len(keys_json.encode("utf-8")) > 65536:
        raise ProductionArtifactTrustConfigError("trusted public key configuration exceeds 64 KiB")
    try:
        encoded_keys = json.loads(keys_json)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ProductionArtifactTrustConfigError("trusted public key configuration must be valid JSON") from exc
    if not isinstance(encoded_keys, dict) or not encoded_keys:
        raise ProductionArtifactTrustConfigError("trusted public key configuration must be a non-empty object")

    trusted_keys: dict[str, bytes] = {}
    for key_id, encoded_key in encoded_keys.items():
        if not isinstance(key_id, str) or not key_id.strip() or key_id.strip() != key_id:
            raise ProductionArtifactTrustConfigError("trusted public key IDs must be non-empty, trimmed strings")
        if key_id.casefold() in _PLACEHOLDER_IDENTITIES:
            raise ProductionArtifactTrustConfigError("trusted public key ID contains a test or placeholder identity")
        if not isinstance(encoded_key, str) or not encoded_key:
            raise ProductionArtifactTrustConfigError(f"public key {key_id!r} must be base64-encoded")
        try:
            raw_key = base64.b64decode(encoded_key, validate=True)
        except (ValueError, TypeError) as exc:
            raise ProductionArtifactTrustConfigError(f"public key {key_id!r} is not valid base64") from exc
        if len(raw_key) != 32:
            raise ProductionArtifactTrustConfigError(f"public key {key_id!r} must decode to 32 raw Ed25519 bytes")
        trusted_keys[key_id] = raw_key

    issuers = _csv_allowlist(env.get("KMH_OIA_ATTESTATION_ALLOWED_ISSUERS"), name="KMH_OIA_ATTESTATION_ALLOWED_ISSUERS")
    subjects = _csv_allowlist(env.get("KMH_OIA_ATTESTATION_ALLOWED_SUBJECTS"), name="KMH_OIA_ATTESTATION_ALLOWED_SUBJECTS")
    source_revision = env.get("KMH_OIA_ATTESTATION_EXPECTED_SOURCE_REVISION", "").strip().lower()
    if len(source_revision) not in (40, 64) or any(char not in "0123456789abcdef" for char in source_revision):
        raise ProductionArtifactTrustConfigError("KMH_OIA_ATTESTATION_EXPECTED_SOURCE_REVISION must be a full 40- or 64-character hexadecimal SHA")

    def required_positive_int(name: str) -> int:
        raw = env.get(name, "")
        try:
            value = int(raw)
        except (TypeError, ValueError) as exc:
            raise ProductionArtifactTrustConfigError(f"{name} must be an integer") from exc
        if value <= 0:
            raise ProductionArtifactTrustConfigError(f"{name} must be greater than zero")
        return value

    return ProductionArtifactTrustConfig(
        trusted_public_keys=trusted_keys,
        allowed_issuers=issuers,
        allowed_subjects=subjects,
        expected_source_revision=source_revision,
        max_age_seconds=required_positive_int("KMH_OIA_ATTESTATION_MAX_AGE_SECONDS"),
        max_clock_skew_seconds=required_positive_int("KMH_OIA_ATTESTATION_MAX_CLOCK_SKEW_SECONDS"),
    )


def load_production_runtime_artifacts(
    classifier_path: str | os.PathLike[str],
    policy_path: str | os.PathLike[str],
    *,
    attestation: RuntimeArtifactAttestation,
    classifier_loader,
    policy_loader,
    environ: Mapping[str, str] | None = None,
) -> VerifiedRuntimeArtifacts:
    """Pin release revision and trust root before reading/loading production artifacts."""
    config = load_production_artifact_trust_config(environ)
    if not isinstance(attestation, RuntimeArtifactAttestation):
        raise ProductionArtifactTrustConfigError("a signed runtime artifact attestation is required")
    if attestation.source_revision.strip().lower() != config.expected_source_revision:
        raise ProductionArtifactTrustConfigError("attestation source revision does not match the configured release revision")
    verifier = config.create_verifier()
    try:
        return verify_and_load_runtime_artifacts(
            classifier_path, policy_path, attestation=attestation, verifier=verifier,
            classifier_loader=classifier_loader, policy_loader=policy_loader,
        )
    except Exception as exc:
        raise ProductionArtifactTrustConfigError("production runtime artifact verification or loading failed closed") from exc
