"""Local execution-evidence binding slice inspired by WIMSE AEE drafts.

This module computes request digests at the serving boundary and links one
execution receipt to one audit decision. It does not implement SCITT, in-toto,
JWS/COSE signatures, a trusted evidence service, or remote transparency proofs.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Any


_GENESIS_HASH = "0" * 64


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
    previous_receipt_hash: str = _GENESIS_HASH

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
            "previous_receipt_hash": self.previous_receipt_hash,
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


class ExecutionEvidenceChain:
    """In-memory hash chain for local verification; not a SCITT transparency log."""

    def __init__(self) -> None:
        self._receipts: list[ExecutionReceipt] = []

    @property
    def receipts(self) -> tuple[ExecutionReceipt, ...]:
        return tuple(self._receipts)

    def append(self, receipt: ExecutionReceipt) -> ExecutionReceipt:
        expected_sequence = len(self._receipts) + 1
        if receipt.sequence != expected_sequence:
            raise ValueError("execution receipt sequence must be contiguous")
        expected_previous = (
            _GENESIS_HASH if not self._receipts
            else self._receipts[-1].receipt_digest
        )
        if receipt.previous_receipt_hash not in {_GENESIS_HASH, expected_previous}:
            raise ValueError("caller-supplied previous receipt hash is not trusted")
        chained = replace(receipt, previous_receipt_hash=expected_previous)
        self._receipts.append(chained)
        return chained

    def verify(self) -> bool:
        previous = _GENESIS_HASH
        for expected_sequence, receipt in enumerate(self._receipts, start=1):
            if receipt.sequence != expected_sequence:
                return False
            if receipt.previous_receipt_hash != previous:
                return False
            previous = receipt.receipt_digest
        return True
