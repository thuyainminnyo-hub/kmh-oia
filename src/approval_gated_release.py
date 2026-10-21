"""Compose QA, source-revision checks, independent approval, and release decision.

Approval authority is injected by the caller. A production authority must verify
its approval record/identity from a trusted store; this helper fails closed when
that authority is missing, unavailable, or out of scope.
"""
from src.approval_policy import ApprovalAuthority, validate_independent_approval
from src.evidence_object import EvidenceObject
from src.governance_gate import ReleaseDecision
from src.qa_gate import QAVerdict


def decide_release_with_approval(
    evidence: EvidenceObject,
    qa_verdict: QAVerdict | None,
    *,
    expected_source_revision: str,
    actual_source_revision: str | None,
    approval_authority: ApprovalAuthority,
    approval_id: str | None,
    signing_service_id: str,
    accepted_policy_ids: set[str],
) -> ReleaseDecision:
    """Create a release decision only after a matching independent approval passes."""
    # The ordinary gate is useful for its non-approval checks, but the boolean
    # approval path must not be used to assert identity here.
    qa_matches = (
        qa_verdict is not None
        and qa_verdict.evidence_id == evidence.evidence_id
        and qa_verdict.status == "PASS"
    )
    revision_matches = (
        isinstance(expected_source_revision, str)
        and bool(expected_source_revision.strip())
        and isinstance(actual_source_revision, str)
        and bool(actual_source_revision.strip())
        and expected_source_revision.strip() == actual_source_revision.strip()
        and evidence.source_revision == actual_source_revision.strip()
        and evidence.source_revision != "unresolved"
    )
    approval_check = validate_independent_approval(
        approval_authority,
        approval_id=approval_id,
        evidence_id=evidence.evidence_id,
        qa_id=qa_verdict.qa_id if qa_verdict else "",
        source_revision=actual_source_revision or "",
        signing_service_id=signing_service_id,
        accepted_policy_ids=accepted_policy_ids,
    )
    checks = [
        {
            "name": "qa_passes_for_same_evidence",
            "passed": qa_matches,
            "detail": "matching QA PASS present" if qa_matches else "missing, failing, or unrelated QA verdict",
        },
        {
            "name": "evidence_has_artifact_and_digest",
            "passed": bool(evidence.artifact_ref and evidence.sha256_digest),
            "detail": "artifact reference and digest present" if evidence.artifact_ref and evidence.sha256_digest else "artifact reference or digest missing",
        },
        {
            "name": "source_revision_matches_runtime",
            "passed": revision_matches,
            "detail": "evidence, expected, and actual source revisions match" if revision_matches else "revision unresolved, unavailable, or not equal to actual runtime revision",
        },
        {
            "name": "independent_approval_verified",
            "passed": approval_check.passed,
            "detail": approval_check.reason,
        },
    ]
    allowed = all(item["passed"] for item in checks)
    return ReleaseDecision(
        decision_id=f"release-decision:{__import__('uuid').uuid4()}",
        evidence_id=evidence.evidence_id,
        qa_id=qa_verdict.qa_id if qa_verdict else None,
        status="ALLOW" if allowed else "BLOCK",
        decided_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat().replace("+00:00", "Z"),
        checks=tuple(checks),
        reason="all release gates passed" if allowed else "one or more release gates failed closed",
        approver_id=approval_check.approver_id,
        source_revision_verified=revision_matches,
    )
