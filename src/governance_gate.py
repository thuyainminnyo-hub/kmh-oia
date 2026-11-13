"""Fail-closed release decision gate for evidence and QA records.

This is a policy decision helper, not an identity provider or deployment service.
It requires callers to supply independently verified source-revision status and
an explicit authenticated approval context. Do not treat self-asserted booleans
from untrusted clients as authentication.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
import uuid

from src.evidence_object import EvidenceObject
from src.qa_gate import QAVerdict


@dataclass(frozen=True)
class ReleaseDecision:
    decision_id: str
    evidence_id: str
    qa_id: str | None
    status: str
    decided_at: str
    checks: tuple[dict[str, Any], ...]
    reason: str
    approver_id: str | None
    source_revision_verified: bool

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["checks"] = [dict(check) for check in self.checks]
        return result


def decide_release(
    evidence: EvidenceObject,
    qa_verdict: QAVerdict | None,
    *,
    expected_source_revision: str,
    actual_source_revision: str | None,
    approval_id: str | None,
    approver_id: str | None,
    approver_authorized: bool,
) -> ReleaseDecision:
    """Issue ALLOW only when evidence, QA, revision, and approval gates pass.

    The caller is responsible for obtaining actual_source_revision from the
    executing checkout and for authenticating/authorizing the approver through
    a trusted identity/policy service. Missing inputs fail closed.
    """
    if not isinstance(evidence, EvidenceObject):
        raise TypeError("evidence must be an EvidenceObject")
    if qa_verdict is not None and not isinstance(qa_verdict, QAVerdict):
        raise TypeError("qa_verdict must be a QAVerdict or None")

    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    qa_matches = (
        qa_verdict is not None
        and qa_verdict.evidence_id == evidence.evidence_id
        and qa_verdict.status == "PASS"
    )
    add("qa_passes_for_same_evidence", qa_matches,
        "matching QA PASS present" if qa_matches else "missing, failing, or unrelated QA verdict")

    digest_available = bool(evidence.sha256_digest and evidence.artifact_ref)
    add("evidence_has_artifact_and_digest", digest_available,
        "artifact reference and digest present" if digest_available else "artifact reference or digest missing")

    revision_matches = (
        isinstance(expected_source_revision, str)
        and bool(expected_source_revision.strip())
        and isinstance(actual_source_revision, str)
        and bool(actual_source_revision.strip())
        and expected_source_revision.strip() == actual_source_revision.strip()
        and evidence.source_revision == actual_source_revision.strip()
        and evidence.source_revision != "unresolved"
    )
    add("source_revision_matches_runtime", revision_matches,
        "evidence, expected, and actual source revisions match" if revision_matches else
        "revision unresolved, unavailable, or not equal to the actual runtime revision")

    approval_complete = (
        isinstance(approval_id, str) and bool(approval_id.strip())
        and isinstance(approver_id, str) and bool(approver_id.strip())
        and approver_authorized is True
    )
    add("authorized_approval_present", approval_complete,
        "approval reference and authorized approver supplied" if approval_complete else
        "approval reference, approver identity, or authorization missing")

    allowed = all(check["passed"] for check in checks)
    return ReleaseDecision(
        decision_id=f"release-decision:{uuid.uuid4()}",
        evidence_id=evidence.evidence_id,
        qa_id=qa_verdict.qa_id if qa_verdict is not None else None,
        status="ALLOW" if allowed else "BLOCK",
        decided_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        checks=tuple(checks),
        reason="all release gates passed" if allowed else "one or more release gates failed closed",
        approver_id=approver_id.strip() if isinstance(approver_id, str) and approver_id.strip() else None,
        source_revision_verified=revision_matches,
    )


def write_decision(decision: ReleaseDecision, path: str | Path) -> None:
    """Append a release decision to a separate JSONL audit file."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(decision.to_dict(), sort_keys=True, ensure_ascii=False) + "\n")
        stream.flush()
