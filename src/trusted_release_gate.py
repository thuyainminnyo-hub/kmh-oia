"""Compose envelope verification with the fail-closed release enforcer.

This layer verifies the envelope body matches its checksum and reconstructs the
decision record. It cannot authenticate the envelope origin. Production use
still requires a trusted, access-controlled storage or digital signature.
"""
from typing import Any

from src.governance_gate import ReleaseDecision
from src.release_envelope import verify_envelope
from src.release_enforcer import require_release_allowed


def require_trusted_release_allowed(envelope: dict[str, Any]) -> ReleaseDecision:
    """Reject malformed/tampered envelopes; then enforce an ALLOW decision."""
    if not verify_envelope(envelope):
        raise ValueError("release decision envelope integrity verification failed")
    try:
        decision = ReleaseDecision(
            decision_id=envelope["decision"]["decision_id"],
            evidence_id=envelope["decision"]["evidence_id"],
            qa_id=envelope["decision"].get("qa_id"),
            status=envelope["decision"]["status"],
            decided_at=envelope["decision"]["decided_at"],
            checks=tuple(envelope["decision"]["checks"]),
            reason=envelope["decision"]["reason"],
            approver_id=envelope["decision"].get("approver_id"),
            source_revision_verified=envelope["decision"]["source_revision_verified"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("release decision envelope has an invalid decision shape") from exc
    require_release_allowed(decision)
    return decision
