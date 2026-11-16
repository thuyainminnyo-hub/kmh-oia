"""Deterministic cross-record validation for synthetic PIE project bundles."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .contracts import AcceptanceCriterion, ContractError, ProjectBrief, Requirement


def _unique(records: Sequence[Any], attr: str, label: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for record in records:
        key = getattr(record, attr)
        if key in result:
            raise ContractError(f"duplicate {label}: {key}")
        result[key] = record
    return result


def validate_project_bundle(
    brief: ProjectBrief,
    requirements: Sequence[Requirement],
    acceptance_criteria: Sequence[AcceptanceCriterion],
    *,
    test_refs: Mapping[str, str] | None = None,
    evidence_refs: Mapping[str, str] | None = None,
    qa_refs: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Validate PRJ→REQ→PAC links and optional downstream TEST→EVD→QA references.

    Downstream registries are intentionally external to this increment; their supplied
    references are checked for presence, not created, authenticated, or persisted here.
    """
    reqs = _unique(requirements, "requirement_id", "requirement_id")
    pacs = _unique(acceptance_criteria, "acceptance_id", "acceptance_id")
    if not requirements:
        raise ContractError("project bundle must contain at least one requirement")
    if not acceptance_criteria:
        raise ContractError("project bundle must contain at least one acceptance criterion")
    for req in requirements:
        if req.project_id != brief.project_id:
            raise ContractError(f"requirement {req.requirement_id} belongs to another project")
    for pac in acceptance_criteria:
        if pac.project_id != brief.project_id:
            raise ContractError(f"acceptance criterion {pac.acceptance_id} belongs to another project")
        for req_id in pac.requirement_ids:
            if req_id not in reqs:
                raise ContractError(f"{pac.acceptance_id} references missing requirement {req_id}")
    uncovered = sorted(set(reqs) - {rid for pac in acceptance_criteria for rid in pac.requirement_ids})
    if uncovered:
        raise ContractError(f"requirements without acceptance coverage: {', '.join(uncovered)}")

    downstream = (test_refs or {}, evidence_refs or {}, qa_refs or {})
    for label, refs in zip(("TEST", "EVD", "QA"), downstream):
        for ref_id, target in refs.items():
            if not isinstance(ref_id, str) or not ref_id.strip() or not isinstance(target, str) or not target.strip():
                raise ContractError(f"{label} references must have non-empty string identifiers and targets")

    return {
        "valid": True,
        "project_id": brief.project_id,
        "brief_version": brief.brief_version,
        "brief_hash": brief.content_hash,
        "requirement_count": len(reqs),
        "acceptance_criterion_count": len(pacs),
        "traceability": "PRJ->REQ->PAC",
        "downstream_reference_counts": {
            "TEST": len(downstream[0]), "EVD": len(downstream[1]), "QA": len(downstream[2])
        },
        "execution_performed": False,
        "approval_granted": False,
    }
