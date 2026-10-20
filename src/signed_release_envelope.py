"""HMAC authentication wrapper for release decision envelopes.

The shared key must come from a trusted secret manager or environment injection.
Do not store it in source control, the envelope, logs, or the Notion project page.
HMAC proves integrity/authenticity only relative to holders of the shared key; it
does not replace policy authorization, non-repudiation, or key rotation.
"""
from dataclasses import asdict, dataclass
import hashlib
import hmac
import json
from typing import Any

from src.release_envelope import create_envelope, verify_envelope
from src.governance_gate import ReleaseDecision
from src.trusted_release_gate import require_trusted_release_allowed


@dataclass(frozen=True)
class SignedDecisionEnvelope:
    envelope: dict[str, Any]
    hmac_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _canonical_bytes(envelope: dict[str, Any]) -> bytes:
    return json.dumps(
        envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sign_decision(decision: ReleaseDecision, key: bytes) -> SignedDecisionEnvelope:
    """Create an envelope and HMAC-SHA256 signature with a caller-supplied key."""
    if not isinstance(key, bytes) or len(key) < 32:
        raise ValueError("HMAC key must be bytes with at least 32 bytes")
    envelope = create_envelope(decision).to_dict()
    signature = hmac.new(key, _canonical_bytes(envelope), hashlib.sha256).hexdigest()
    return SignedDecisionEnvelope(envelope=envelope, hmac_sha256=signature)


def verify_signed_envelope(
    signed: SignedDecisionEnvelope | dict[str, Any], key: bytes
) -> bool:
    """Verify HMAC and inner checksum; malformed values fail closed."""
    if not isinstance(key, bytes) or len(key) < 32:
        return False
    if isinstance(signed, SignedDecisionEnvelope):
        value = signed.to_dict()
    elif isinstance(signed, dict):
        value = signed
    else:
        return False
    envelope = value.get("envelope")
    signature = value.get("hmac_sha256")
    if not isinstance(envelope, dict) or not isinstance(signature, str):
        return False
    expected = hmac.new(key, _canonical_bytes(envelope), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return False
    return verify_envelope(envelope)


def require_signed_release_allowed(
    signed: SignedDecisionEnvelope | dict[str, Any], key: bytes
) -> ReleaseDecision:
    """Authenticate the signed envelope first, then enforce the release decision."""
    if not verify_signed_envelope(signed, key):
        raise ValueError("release decision signature or integrity verification failed")
    signed_value = signed.to_dict() if isinstance(signed, SignedDecisionEnvelope) else signed
    return require_trusted_release_allowed(signed_value["envelope"])
