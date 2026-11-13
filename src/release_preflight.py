"""Release preflight that discovers source revision from the active checkout.

This is an orchestration helper for a protected release entrypoint. It obtains
the actual HEAD from Git instead of trusting an actual_revision string supplied
by a caller, rejects a dirty checkout, creates the approval-gated decision, and
requires a signed release to be verified through the key-provider path separately.
"""
from pathlib import Path

from src.approval_gated_release import decide_release_with_approval
from src.approval_policy import ApprovalAuthority
from src.evidence_object import EvidenceObject
from src.governance_gate import ReleaseDecision
from src.qa_gate import QAVerdict
from src.source_revision import require_verified_source_revision


def preflight_release(
    evidence: EvidenceObject,
    qa_verdict: QAVerdict | None,
    *,
    expected_source_revision: str,
    checkout_root: str | Path,
    approval_authority: ApprovalAuthority,
    approval_id: str | None,
    signing_service_id: str,
    accepted_policy_ids: set[str],
) -> ReleaseDecision:
    """Create a fail-closed release decision using revision discovered from Git."""
    actual_revision = require_verified_source_revision(
        expected_revision=expected_source_revision,
        root=checkout_root,
    )
    if evidence.source_revision != actual_revision:
        # Do not allow evidence created by another revision, even if the
        # expected build revision matched the current checkout.
        from src.governance_gate import ReleaseDecision
        from datetime import datetime, timezone
        import uuid
        return ReleaseDecision(
            decision_id=f"release-decision:{uuid.uuid4()}",
            evidence_id=evidence.evidence_id,
            qa_id=qa_verdict.qa_id if qa_verdict else None,
            status="BLOCK",
            decided_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            checks=(
                {"name":"source_revision_matches_evidence","passed":False,
                 "detail":"evidence source revision does not match actual checkout HEAD"},
            ),
            reason="evidence source revision does not match actual checkout HEAD",
            approver_id=None,
            source_revision_verified=False,
        )
    return decide_release_with_approval(
        evidence,
        qa_verdict,
        expected_source_revision=expected_source_revision,
        actual_source_revision=actual_revision,
        approval_authority=approval_authority,
        approval_id=approval_id,
        signing_service_id=signing_service_id,
        accepted_policy_ids=accepted_policy_ids,
    )
