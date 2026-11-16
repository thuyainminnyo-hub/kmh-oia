"""Deterministic cross-record validation for synthetic PIE project bundles."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .contracts import AcceptanceCriterion, ContractError, ProjectBrief, Requirement


def _is_record_sequence(records: Any) -> bool:
    """Return whether records is a supported, non-text sequence."""
    return isinstance(records, Sequence) and not isinstance(records, (str, bytes, bytearray))


def _unique(
    records: Sequence[Any],
    attr: str,
    label: str,
    record_type: type[Any],
) -> dict[str, Any]:
    """Validate a record sequence and index it by a unique, non-empty string field."""
    if not _is_record_sequence(records):
        raise ContractError(f"{label} records must be a non-text sequence")
    if not isinstance(attr, str) or not attr.strip():
        raise ContractError("record identifier attribute must be a non-empty string")
    if not isinstance(label, str) or not label.strip():
        raise ContractError("record label must be a non-empty string")
    if not isinstance(record_type, type):
        raise ContractError("record type must be a valid type")

    result: dict[str, Any] = {}
    for record in records:
        if not isinstance(record, record_type):
            raise ContractError(f"{label} records must contain {record_type.__name__} instances")
        key = getattr(record, attr, None)
        if not isinstance(key, str) or not key.strip():
            raise ContractError(f"{label} identifiers must be non-empty strings")
        if key in result:
            raise ContractError(f"duplicate {label}: {key}")
        result[key] = record
    return result


def _validate_reference_mapping(label: str, refs: Mapping[str, str] | None) -> int:
    """Validate optional downstream references without creating or persisting records."""
    if refs is None:
        return 0
    if not isinstance(refs, Mapping):
        raise ContractError(f"{label} references must be a mapping or None")

    count = 0
    for ref_id, target in refs.items():
        if (
            not isinstance(ref_id, str)
            or not ref_id.strip()
            or not isinstance(target, str)
            or not target.strip()
        ):
            raise ContractError(
                f"{label} references must have non-empty string identifiers and targets"
            )
        count += 1
    return count


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
    references are checked for shape and presence, not created, authenticated, or persisted.
    Invalid input is rejected at this boundary with ContractError.
    """
    if not isinstance(brief, ProjectBrief):
        raise ContractError("brief must be a ProjectBrief")
    if not _is_record_sequence(requirements):
        raise ContractError("requirements must be a non-text sequence")
    if not _is_record_sequence(acceptance_criteria):
        raise ContractError("acceptance_criteria must be a non-text sequence")

    reqs = _unique(requirements, "requirement_id", "requirement_id", Requirement)
    pacs = _unique(
        acceptance_criteria, "acceptance_id", "acceptance_id", AcceptanceCriterion
    )
    if not reqs:
        raise ContractError("project bundle must contain at least one requirement")
    if not pacs:
        raise ContractError("project bundle must contain at least one acceptance criterion")

    for req in reqs.values():
        if req.project_id != brief.project_id:
            raise ContractError(f"requirement {req.requirement_id} belongs to another project")
    for pac in pacs.values():
        if pac.project_id != brief.project_id:
            raise ContractError(
                f"acceptance criterion {pac.acceptance_id} belongs to another project"
            )
        for req_id in pac.requirement_ids:
            if req_id not in reqs:
                raise ContractError(
                    f"{pac.acceptance_id} references missing requirement {req_id}"
                )

    uncovered = sorted(
        set(reqs)
        - {req_id for pac in pacs.values() for req_id in pac.requirement_ids}
    )
    if uncovered:
        raise ContractError(
            f"requirements without acceptance coverage: {', '.join(uncovered)}"
        )

    test_count = _validate_reference_mapping("TEST", test_refs)
    evidence_count = _validate_reference_mapping("EVD", evidence_refs)
    qa_count = _validate_reference_mapping("QA", qa_refs)

    return {
        "valid": True,
        "project_id": brief.project_id,
        "brief_version": brief.brief_version,
        "brief_hash": brief.content_hash,
        "requirement_count": len(reqs),
        "acceptance_criterion_count": len(pacs),
        "traceability": "PRJ->REQ->PAC",
        "downstream_reference_counts": {
            "TEST": test_count,
            "EVD": evidence_count,
            "QA": qa_count,
        },
        "execution_performed": False,
        "approval_granted": False,
    }
