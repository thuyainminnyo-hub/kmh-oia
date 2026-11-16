"""In-memory, synthetic-only project contract registry (not a production datastore)."""

from __future__ import annotations

from .contracts import AcceptanceCriterion, ContractError, ProjectBrief, ProjectStatus, Requirement
from .validation import validate_project_bundle


class ProjectRegistry:
    def __init__(self) -> None:
        self._briefs: dict[str, ProjectBrief] = {}
        self._brief_versions: dict[str, dict[int, ProjectBrief]] = {}
        self._requirements: dict[str, dict[str, Requirement]] = {}
        self._criteria: dict[str, dict[str, AcceptanceCriterion]] = {}
        # This binds each approval reference to one immutable project/version/content tuple.
        # It is a synthetic integrity guard, not authenticated or cryptographic approval.
        self._approval_bindings: dict[str, tuple[str, int, str]] = {}

    def register(self, brief: ProjectBrief) -> None:
        if not isinstance(brief, ProjectBrief):
            raise ContractError("brief must be a ProjectBrief")
        existing = self._briefs.get(brief.project_id)
        if existing is not None and brief.brief_version <= existing.brief_version:
            raise ContractError("brief versions must increase; prior versions are retained")

        if brief.status in (ProjectStatus.APPROVED, ProjectStatus.ACTIVE):
            # ProjectBrief enforces non-empty approval_ref for these statuses.
            approval_ref = brief.approval_ref
            if approval_ref in self._approval_bindings:
                raise ContractError("approval references are immutable and cannot be reused")
            binding = (brief.project_id, brief.brief_version, brief.content_hash)
            self._approval_bindings[approval_ref] = binding

        self._brief_versions.setdefault(brief.project_id, {})[brief.brief_version] = brief
        self._briefs[brief.project_id] = brief
        self._requirements.setdefault(brief.project_id, {})
        self._criteria.setdefault(brief.project_id, {})

    def get_brief_version(self, project_id: str, version: int) -> ProjectBrief:
        try:
            return self._brief_versions[project_id][version]
        except KeyError as exc:
            raise ContractError(f"unknown project brief version: {project_id} v{version}") from exc

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
