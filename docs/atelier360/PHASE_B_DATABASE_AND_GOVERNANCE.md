# ATELIER 360 — Phase B Database & Governance Contract

Status: design specification; not deployed. Scope: isolated PostgreSQL sandbox first.
Owner decision: PostgreSQL; existing NAYRA MAISON product; full foundation; controlled autonomy.

## Repository integration
The existing KMH OIA runtime exposes security policy, governed-tool execution, state and tracing boundaries. The Fashion module must integrate through those boundaries; it must not bypass them or directly invoke production systems.

## Agent registry seed catalogue
Register these as proposed agents, not active production identities:
- FAS-RESEARCH: research, sources, product brief; read/prepare only.
- FAS-DESIGN: design drafts and specification proposals; no design freeze.
- FAS-PATTERN: pattern drafts and measurement analysis; no pattern release.
- FAS-PRODUCTION: BOM and work-order preparation; no production start or quantity amendment.
- FAS-QUALITY: inspection evidence collation; no self-approval of its own generated evidence.
- FAS-TRACEABILITY: model/batch/item lineage and DPP draft; no public publishing.

Every deployed agent identity must be bound to a workload identity outside prompt text. Never treat an agent-supplied agent_id as authentication. Verify identity at the API gateway and map verified subject to agent_registry.

## Permission catalogue
Suggested codes:
- fashion.model.read (P0)
- fashion.model.draft.write (P2)
- fashion.design.propose (P1/P2)
- fashion.design.approve (P3; human only)
- fashion.pattern.propose (P1/P2)
- fashion.pattern.release (P3; human technical authority)
- fashion.bom.propose (P1/P2)
- fashion.batch.prepare (P1/P2)
- fashion.production.start (P3; human approval)
- fashion.production.quantity.change (P3; human approval)
- fashion.qa.inspect (P1/P2; evidence required)
- fashion.qa.release (P3; independent authorized human)
- fashion.item.trace.read (P0)
- fashion.dpp.publish (P3; human approval)
- fashion.ip.rights.change (P4 for agents; legal/owner human process only)

Default deny. No standing write privilege for consequential actions. Grants must be task-scoped, expire, and be revocable. Application database roles must not own tables and must not have BYPASSRLS. RLS policies are tenant-specific and must be added only after authenticated tenant context is designed; do not deploy a permissive placeholder policy.

## Approval protocol
1. Agent submits a proposal with subject, requested action, expected before-state/version, input references and idempotency key.
2. Gateway authenticates workload identity and resolves the registered agent.
3. Policy engine checks status, tool allowlist, resource scope, grant expiry, risk and required approval.
4. If approval is required, create a pending approval; do not execute the action.
5. A distinct authorized human reviews the exact proposal and approves/rejects it. Approval binds to proposal hash, subject version, action and expiry.
6. Execution service rechecks approval, current version, grant and idempotency key inside one transaction.
7. Write business state and event record atomically. Append evidence references; no silent overwrite.
8. Independent QA validates evidence. Release is a separate human-controlled action.

Approvals are single-use, subject/version/action-bound, expire quickly, and cannot authorize a modified proposal. A new proposal requires new approval. Agent may not approve its own proposal.

## Evidence ledger contract
For every controlled action capture: event_id, organization_id, event_code, subject_type/id, verified actor or agent, occurred_at, correlation_id, idempotency_key, approval_id, evidence_id, payload schema version, before/after references, result, previous_hash and event_hash.
Hash canonical event content with a documented canonical JSON encoding and SHA-256. A hash chain is tamper-evident, not proof against a database superuser; export signed checkpoints to independently controlled immutable storage. Do not store secrets, access tokens, full customer personal data, or unredacted prompts in event payloads.

## Data rules
- Model -> Batch -> Individual Item is the authoritative hierarchy.
- Batch locks exact design, pattern and BOM version references.
- Quantity and material allocation changes after approval require a new approval and event.
- Unknown values remain NULL/UNKNOWN; never synthesize supplier, composition, origin, care, certification or rights claims.
- DPP is draft until evidence completeness and human publication approval.
- Use a separate storage service for binary patterns/photos; store URI, digest, access classification and evidence metadata in PostgreSQL.

## API contract principles
- All write operations require authenticated human or workload identity.
- Agent identity is derived from validated credential, never request body.
- Require Idempotency-Key on mutating endpoints.
- Require If-Match/version precondition on approval and execution.
- Return 202 for approval-pending proposals; no execution occurs.
- Return 403 for policy denial, 409 for stale version/duplicate conflict, 422 for invalid state transition.
- Use correlation IDs and structured error codes.
- Never expose internal evidence storage URLs publicly; issue short-lived scoped access URLs after authorization.

## Deployment controls
- Dedicated non-production database and credentials.
- Migration role separate from runtime role.
- Runtime role has no schema ownership, no superuser, no BYPASSRLS, no DDL.
- Backups encrypted; restore test required.
- TLS in transit and encryption at rest managed by infrastructure.
- Secrets from a secret manager, never committed to Git.
- Enable RLS and explicit tenant policies before multi-tenant or shared production use.
- Migration rollback plan and tested backup restore before any production migration.

## Acceptance gates
- Migration applies to clean PostgreSQL sandbox.
- Constraints reject invalid model/batch/item relationships and invalid quantities.
- Evidence and production events reject UPDATE/DELETE for runtime roles.
- Expired/revoked grants and missing approvals are denied.
- Stale version and duplicate idempotency key cannot execute twice.
- Approval cannot be reused or altered to authorize a different proposal.
- Agent cannot approve its own proposal.
- QA pass requires linked evidence.
- DPP publish requires human approval and required evidence.
- RLS tenant isolation tests pass using non-owner runtime role.
- Restore and recovery tests pass.
