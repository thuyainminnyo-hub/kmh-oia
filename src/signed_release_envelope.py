"""HMAC authentication for release decision envelopes with key identifiers.

Keys must come from trusted secret management. Never commit keys or store them in
the envelope. HMAC authenticates a message relative to shared-key holders; it is
not a public-key signature and does not implement key storage or rotation policy.
"""
from dataclasses import asdict, dataclass
import hashlib
import hmac
import json
from typing import Any, Mapping, AbstractSet

from src.release_envelope import create_envelope, verify_envelope
from src.governance_gate import ReleaseDecision
from src.trusted_release_gate import require_trusted_release_allowed


@dataclass(frozen=True)
class SignedDecisionEnvelope:
    envelope: dict[str, Any]
    hmac_sha256: str
    key_id: str = "default"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _canonical_bytes(envelope: dict[str, Any], key_id: str) -> bytes:
    # Bind key_id into the signed material so it cannot be swapped independently.
    return json.dumps(
        {"key_id": key_id, "envelope": envelope},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sign_decision(
    decision: ReleaseDecision,
    key: bytes,
    key_id: str = "default",
) -> SignedDecisionEnvelope:
    """Sign with a caller-supplied key and stable non-secret key identifier."""
    if not isinstance(key, bytes) or len(key) < 32:
        raise ValueError("HMAC key must be bytes with at least 32 bytes")
    if not isinstance(key_id, str) or not key_id.strip():
        raise ValueError("key_id must be a nonblank string")
    if not isinstance(decision, ReleaseDecision):
        raise TypeError("decision must be a ReleaseDecision")
    envelope = create_envelope(decision).to_dict()
    signature = hmac.new(
        key, _canonical_bytes(envelope, key_id), hashlib.sha256
    ).hexdigest()
    return SignedDecisionEnvelope(envelope=envelope, hmac_sha256=signature, key_id=key_id)


def _as_dict(signed: SignedDecisionEnvelope | dict[str, Any]) -> dict[str, Any] | None:
    if isinstance(signed, SignedDecisionEnvelope):
        return signed.to_dict()
    if isinstance(signed, dict):
        return signed
    return None


def verify_signed_envelope(
    signed: SignedDecisionEnvelope | dict[str, Any],
    key: bytes,
    expected_key_id: str | None = None,
) -> bool:
    """Verify HMAC and inner checksum; mismatched key IDs fail closed."""
    if not isinstance(key, bytes) or len(key) < 32:
        return False
    value = _as_dict(signed)
    if value is None:
        return False
    envelope = value.get("envelope")
    signature = value.get("hmac_sha256")
    key_id = value.get("key_id")
    if not isinstance(envelope, dict) or not isinstance(signature, str):
        return False
    if not isinstance(key_id, str) or not key_id.strip():
        return False
    if expected_key_id is not None and key_id != expected_key_id:
        return False
    expected = hmac.new(
        key, _canonical_bytes(envelope, key_id), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected) and verify_envelope(envelope)


def verify_with_keyring(
    signed: SignedDecisionEnvelope | dict[str, Any],
    keyring: Mapping[str, bytes],
    accepted_key_ids: AbstractSet[str],
) -> bool:
    """Verify using the key selected by key_id, if that ID remains accepted.

    During rotation, include the active key and any explicitly accepted retiring
    keys in accepted_key_ids. After the retirement window, remove the old ID.
    """
    value = _as_dict(signed)
    if value is None:
        return False
    key_id = value.get("key_id")
    if not isinstance(key_id, str) or key_id not in accepted_key_ids:
        return False
    key = keyring.get(key_id)
    if not isinstance(key, bytes):
        return False
    return verify_signed_envelope(value, key, expected_key_id=key_id)


def require_signed_release_allowed(
    signed: SignedDecisionEnvelope | dict[str, Any], key: bytes
) -> ReleaseDecision:
    """Authenticate the envelope first, then enforce the release decision."""
    if not verify_signed_envelope(signed, key):
        raise ValueError("release decision signature or integrity verification failed")
    value = _as_dict(signed)
    assert value is not None
    return require_trusted_release_allowed(value["envelope"])


def require_release_allowed_with_keyring(
    signed: SignedDecisionEnvelope | dict[str, Any],
    keyring: Mapping[str, bytes],
    accepted_key_ids: AbstractSet[str],
) -> ReleaseDecision:
    """Apply accepted-key rotation policy, then enforce the decision."""
    if not verify_with_keyring(signed, keyring, accepted_key_ids):
        raise ValueError("release decision signature invalid or key_id retired/untrusted")
    value = _as_dict(signed)
    assert value is not None
    return require_trusted_release_allowed(value["envelope"])
