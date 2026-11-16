# PIE V1-INC-001 — Synthetic Contract Layer

**Status:** Implemented on an isolated feature branch; tests not run; no release approval.

## Owner decisions applied
- PAC identifiers use `PAC-PRJ-NNN-NNN`; global `AC-01`–`AC-10` remain reserved for global KMH OIA acceptance criteria.
- Canonical traceability direction: `PRJ → REQ → PAC → TEST → EVD → QA`.
- This increment is limited to synthetic-only Project Brief, Requirement, Project Acceptance Criterion (PAC), and deterministic contract validation.
- Implementation authorization applies only to this increment and does not authorize merge, release, deployment, external integrations, or production use.

## Included
- Immutable Python dataclasses for ProjectBrief, Requirement, and AcceptanceCriterion.
- Canonical SHA-256 content hash for project briefs.
- Strict identifier, enum, version, approval-reference, and synthetic-environment checks.
- In-memory registry with unique immutable IDs and increasing brief versions.
- Cross-record validation for project ownership, requirement references, PAC coverage, and optional downstream TEST/EVD/QA reference shape.
- Unit tests authored but **not executed**.

## Traceability boundary
This increment validates `PRJ → REQ → PAC`. TEST, EVD, and QA registries and their lifecycle/authenticity are not implemented here. Optional downstream references are shape-checked only; they are not proof that tests ran, evidence exists, QA passed, or a reviewer approved anything.

## Explicit exclusions preserved
- No production or customer data; synthetic fixtures only.
- No production database, migrations, cloud provisioning, or persistence beyond process memory.
- No OIDC/IdP, authenticated-principal verification, tenant isolation, RBAC activation, or delegation implementation.
- No KMS, secrets, external API/provider adapters, network calls, or external side effects.
- No test execution, CI run, merge, PR creation, deployment, release promotion, or production operation.
- No claims of test pass, end-to-end execution, independent assurance, or production readiness.

## Validation semantics
- Invalid IDs, duplicate IDs, cross-project references, missing REQ links, and uncovered requirements raise `ContractError`.
- APPROVED/ACTIVE briefs require an approval reference. This field is only a reference string; it does not authenticate an approver or constitute authorization.
- `requested_environment` is untrusted descriptive input. `effective_environment` is restricted to `local_synthetic` or `isolated_cloud_sandbox`.
- The brief hash covers canonical brief fields including version, status, and approval reference. Any material change requires a new version and recomputed hash.
- Registry is in-memory and intended only for synthetic contract validation.

## Next gate
Review the branch diff, authorize test execution separately, then review test evidence. Human owner approval remains required before any merge or release action.
