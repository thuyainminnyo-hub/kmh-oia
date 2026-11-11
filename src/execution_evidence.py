"""Local execution-evidence binding slice inspired by WIMSE AEE drafts.

This module computes request digests at the serving boundary and links one
execution receipt to one audit decision. It does not implement SCITT, in-toto,
JWS/COSE signatures, a trusted evidence service, or remote transparency proofs.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


def canonical_json(value: Any) -> bytes:
    """Deterministic JSON serialization for this local prototype."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class AgentEvidenceClaim:
    evidence_service: str
    policy_pack_digest: str
    logical_agent_id: str
    assurance_statement_digest: str | None = None

    def validate_shape(self) -> bool:
        required = (self.evidence_service, self.policy_pack_digest, self.logical_agent_id)
        if not all(isinstance(v, str) and v.strip() for v in required):
            return False
        if len(self.policy_pack_digest) != 64:
            return False
        try:
            int(self.policy_pack_digest, 16)
        except ValueError:
            return False
        if self.assurance_statement_digest is not None:
            if len(self.assurance_statement_digest) != 64:
                return False
            try:
                int(self.assurance_statement_digest, 16)
            except ValueError:
                return False
        return True


@dataclass(frozen=True)
class ExecutionReceipt:
    sequence: int
    request_id: str
    logical_agent_id: str
    runtime_agent_id: str
    evidence_service: str
    policy_pack_digest: str
    request_digest: str
    resource: str
    tool: str
    action: str
    decision: str
    reason_code: str
    occurred_at_epoch: int
    output_digest: str | None = None

    def canonical_payload(self) -> bytes:
        return canonical_json({
            "sequence": self.sequence,
            "request_id": self.request_id,
            "logical_agent_id": self.logical_agent_id,
            "runtime_agent_id": self.runtime_agent_id,
            "evidence_service": self.evidence_service,
            "policy_pack_digest": self.policy_pack_digest,
            "request_digest": self.request_digest,
            "resource": self.resource,
            "tool": self.tool,
            "action": self.action,
            "decision": self.decision,
            "reason_code": self.reason_code,
            "occurred_at_epoch": self.occurred_at_epoch,
            "output_digest": self.output_digest,
        })

    @property
    def receipt_digest(self) -> str:
        return sha256_hex(self.canonical_payload())


@dataclass(frozen=True)
class VerifiedExecutionLink:
    request_digest: str
    receipt_digest: str
    audit_event_sequence: int
    request_id: str


def build_execution_receipt(
    *,
    claim: AgentEvidenceClaim,
    request: dict[str, Any],
    request_id: str,
    runtime_agent_id: str,
    sequence: int,
    resource: str,
    tool: str,
    action: str,
    decision: str,
    reason_code: str,
    occurred_at_epoch: int,
    output: bytes | None = None,
) -> ExecutionReceipt:
    """Build a receipt using a digest computed from the actual received request."""
    if not claim.validate_shape():
        raise ValueError("invalid agent evidence claim")
    if not request_id.strip() or not runtime_agent_id.strip():
        raise ValueError("request and runtime identity are required")
    if sequence < 1 or occurred_at_epoch < 0:
        raise ValueError("invalid sequence or timestamp")
    if decision not in {"allow", "deny", "indeterminate"}:
        raise ValueError("unsupported authorization decision")
    if not all(v.strip() for v in (resource, tool, action, reason_code)):
        raise ValueError("resource, tool, action and reason code are required")
    return ExecutionReceipt(
        sequence=sequence,
        request_id=request_id,
        logical_agent_id=claim.logical_agent_id,
        runtime_agent_id=runtime_agent_id,
        evidence_service=claim.evidence_service,
        policy_pack_digest=claim.policy_pack_digest,
        request_digest=sha256_hex(canonical_json(request)),
        resource=resource,
        tool=tool,
        action=action,
        decision=decision,
        reason_code=reason_code,
        occurred_at_epoch=occurred_at_epoch,
        output_digest=sha256_hex(output) if output is not None else None,
    )


def verify_execution_link(
    *,
    receipt: ExecutionReceipt,
    actual_request: dict[str, Any],
    actual_request_id: str,
    audit_event_sequence: int,
    expected_logical_agent_id: str,
    expected_runtime_agent_id: str,
    expected_evidence_service: str,
    expected_policy_pack_digest: str,
) -> VerifiedExecutionLink | None:
    """Verify per-call binding; never trust a caller-supplied digest as input."""
    computed_request_digest = sha256_hex(canonical_json(actual_request))
    if receipt.request_id != actual_request_id:
        return None
    if receipt.request_digest != computed_request_digest:
        return None
    if receipt.logical_agent_id != expected_logical_agent_id:
        return None
    if receipt.runtime_agent_id != expected_runtime_agent_id:
        return None
    if receipt.evidence_service != expected_evidence_service:
        return None
    if receipt.policy_pack_digest != expected_policy_pack_digest:
        return None
    if receipt.sequence != audit_event_sequence or audit_event_sequence < 1:
        return None
    return VerifiedExecutionLink(
        request_digest=computed_request_digest,
        receipt_digest=receipt.receipt_digest,
        audit_event_sequence=audit_event_sequence,
        request_id=actual_request_id,
    )
