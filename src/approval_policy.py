"""Independent release-approval policy contract.

This module validates approval assertions supplied by a trusted identity/policy
adapter. It does not authenticate identities itself and must not accept raw
caller booleans from untrusted inputs in production.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol, AbstractSet


@dataclass(frozen=True)
class ApprovalRecord:
    approval_id: str
    approver_id: str
    evidence_id: str
    qa_id: str
    source_revision: str
    decision: str
    policy_id: str
    approved_at: str


class ApprovalAuthority(Protocol):
    """Identity/policy service contract for independent release approval."""

    def resolve_approval(self, approval_id: str) -> ApprovalRecord | None:
        """Load a verified approval record by ID, or return None if untrusted."""
        ...

    def is_authorized_approver(self, approver_id: str, policy_id: str) -> bool:
        """Check identity and permission using a trusted identity/policy system."""
        ...


@dataclass(frozen=True)
class ApprovalCheck:
    passed: bool
    reason: str
    approval_id: str | None
    approver_id: str | None
    policy_id: str | None


def validate_independent_approval(
    authority: ApprovalAuthority,
    *,
    approval_id: str | None,
    evidence_id: str,
    qa_id: str,
    source_revision: str,
    signing_service_id: str,
    accepted_policy_ids: AbstractSet[str],
) -> ApprovalCheck:
    """Require a separate approver, matching approval scope, and accepted policy."""
    if not isinstance(approval_id, str) or not approval_id.strip():
        return ApprovalCheck(False, "approval reference missing", None, None, None)
    try:
        record = authority.resolve_approval(approval_id.strip())
    except Exception:
        return ApprovalCheck(False, "approval authority unavailable", approval_id, None, None)
    if not isinstance(record, ApprovalRecord):
        return ApprovalCheck(False, "approval record missing or untrusted", approval_id, None, None)
    if record.decision != "APPROVE":
        return ApprovalCheck(False, "approval decision is not APPROVE", record.approval_id, record.approver_id, record.policy_id)
    if record.approval_id != approval_id.strip():
        return ApprovalCheck(False, "approval ID mismatch", record.approval_id, record.approver_id, record.policy_id)
    if record.evidence_id != evidence_id or record.qa_id != qa_id:
        return ApprovalCheck(False, "approval does not match evidence/QA scope", record.approval_id, record.approver_id, record.policy_id)
    if record.source_revision != source_revision or not source_revision or source_revision == "unresolved":
        return ApprovalCheck(False, "approval source revision mismatch or unresolved", record.approval_id, record.approver_id, record.policy_id)
    if record.approver_id == signing_service_id:
        return ApprovalCheck(False, "approver must be independent from signing service", record.approval_id, record.approver_id, record.policy_id)
    if record.policy_id not in accepted_policy_ids:
        return ApprovalCheck(False, "approval policy is not accepted", record.approval_id, record.approver_id, record.policy_id)
    try:
        authorized = authority.is_authorized_approver(record.approver_id, record.policy_id)
    except Exception:
        return ApprovalCheck(False, "authorization authority unavailable", record.approval_id, record.approver_id, record.policy_id)
    if authorized is not True:
        return ApprovalCheck(False, "approver is not authorized", record.approval_id, record.approver_id, record.policy_id)
    if not record.approved_at:
        return ApprovalCheck(False, "approval timestamp missing", record.approval_id, record.approver_id, record.policy_id)
    return ApprovalCheck(True, "independent approval record verified", record.approval_id, record.approver_id, record.policy_id)
