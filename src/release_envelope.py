"""Integrity envelope for release decisions.

A SHA-256 checksum detects accidental or unkeyed edits only when the expected
digest is kept in a trusted place. It is not a digital signature and does not
authenticate the decision issuer. Production must persist the envelope and its
digest in a trusted, access-controlled system or use a signed envelope.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any

from src.governance_gate import ReleaseDecision


@dataclass(frozen=True)
class DecisionEnvelope:
    schema_version: str
    decision: dict[str, Any]
    decision_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def create_envelope(decision: ReleaseDecision) -> DecisionEnvelope:
    """Create a stable JSON representation and checksum for a release decision."""
    if not isinstance(decision, ReleaseDecision):
        raise TypeError("decision must be a ReleaseDecision")
    encoded = json.dumps(
        decision.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return DecisionEnvelope(
        schema_version="1.0",
        decision=decision.to_dict(),
        decision_sha256=hashlib.sha256(encoded).hexdigest(),
    )


def verify_envelope(envelope: DecisionEnvelope | dict[str, Any]) -> bool:
    """Return true only for well-shaped envelopes whose decision checksum matches."""
    if isinstance(envelope, DecisionEnvelope):
        value = envelope.to_dict()
    elif isinstance(envelope, dict):
        value = envelope
    else:
        return False
    if value.get("schema_version") != "1.0":
        return False
    decision = value.get("decision")
    expected_digest = value.get("decision_sha256")
    if not isinstance(decision, dict) or not isinstance(expected_digest, str):
        return False
    encoded = json.dumps(
        decision, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    actual_digest = hashlib.sha256(encoded).hexdigest()
    return actual_digest == expected_digest
