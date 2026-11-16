"""In-memory, synthetic-only project contract registry (not a production datastore)."""

from __future__ import annotations

from .contracts import AcceptanceCriterion, ContractError, ProjectBrief, Requirement
from .validation import validate_project_bundle


class ProjectRegistry:
    def __init__(self) -> None:
        self._briefs: dict[str, ProjectBrief] = {}
        self._requirements: dict[str, dict[str, Requirement]] = {}
        self._criteria: dict[str, dict[str, AcceptanceCriterion]] = {}

    def register(self, brief: ProjectBrief) -> None:
        existing = self._briefs.get(brief.project_id)
        if existing is not None:
            if brief.brief_version <= existing.brief_version:
                raise ContractError("brief versions must increase; existing records are not overwritten")
            if brief.status.value in ("APPROVED", "ACTIVE") and brief.approval_ref != existing.approval_ref:
                raise ContractError("a changed brief requires a new approval reference")
        self._briefs[brief.project_id] = brief
        self._requirements.setdefault(brief.project_id, {})
        self._criteria.setdefault(brief.project_id, {})

    def add_requirement(self, requirement: Requirement) -> None:
        if requirement.project_id not in self._briefs:
            raise ContractError("register the project brief before its requirements")
        bucket = self._requirements[requirement.project_id]
        if requirement.requirement_id in bucket:
            raise ContractError("requirement identifiers are immutable and cannot be reused")
        bucket[requirement.requirement_id] = requirement

    def add_acceptance_criterion(self, criterion: AcceptanceCriterion) -> None:
        if criterion.project_id not in self._briefs:
            raise ContractError("register the project brief before acceptance criteria")
        bucket = self._criteria[criterion.project_id]
        if criterion.acceptance_id in bucket:
            raise ContractError("acceptance identifiers are immutable and cannot be reused")
        bucket[criterion.acceptance_id] = criterion

    def validate(self, project_id: str) -> dict[str, object]:
        if project_id not in self._briefs:
            raise ContractError(f"unknown project: {project_id}")
        return validate_project_bundle(
            self._briefs[project_id],
            tuple(self._requirements[project_id].values()),
            tuple(self._criteria[project_id].values()),
        )
