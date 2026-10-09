# KMH Reusable Data Governance Blueprint v1.0

**Classification:** Reusable Architecture / Data Governance / QA Contract  
**Status:** DESIGN DEFINED — IMPLEMENTATION NOT VERIFIED  
**Applies to:** Any KMH dataset that changes over time, including Character Bibles, Prompt Library, Production Memory, route-like structured data, and external research records.

## 1. Purpose
Define how KMH turns changing data into trusted, versioned, reviewable, and reusable knowledge without confusing editable drafts with canonical approved truth.

## 2. Governing Principle
**Editable ≠ Validated. Stored ≠ Canonical. Approved ≠ Runtime Executed.**

Operating Intelligence Architecture is the Brain that defines policy. KMH Operating Organism is the whole system that applies policy across Memory, Nervous System, Immune System, and Execution layers.

## 3. Canonical Data Lifecycle
1. **INGEST** — accept a proposal, source file, observation, or external reference.
2. **IDENTIFY** — assign stable entity IDs and a schema version.
3. **PROVENANCE** — record source, contributor, timestamp, and evidence references.
4. **VALIDATE** — check schema, required fields, references, duplicates, and constraints.
5. **REVIEW** — evaluate correctness, completeness, conflicts, and uncertainty.
6. **APPROVE** — an authorized reviewer makes a separate approval decision.
7. **PUBLISH** — promote an immutable version to the canonical dataset.
8. **DISTRIBUTE** — expose approved snapshots/API/export with version metadata.
9. **MONITOR** — detect stale data, consumer failures, and reported errors.
10. **REVISE / ROLLBACK** — create a new version or restore a previous approved version without erasing history.

## 4. Required Dataset Metadata
- `dataset_id`: stable dataset identity.
- `schema_version`: version of the data contract.
- `dataset_version`: immutable release identifier.
- `status`: draft / in_review / approved / retired / rejected.
- `source_refs`: source records supporting the data.
- `created_at`, `updated_at`, `effective_from` where relevant.
- `proposed_by`, `reviewed_by`, `approved_by` where applicable.
- `change_summary`: human-readable description of what changed and why.
- `validation_result`: checks performed and results.
- `evidence_refs`: links to supporting observations or artifacts.

Only include fields that make sense for a specific dataset; this is a reusable contract, not a mandate to add meaningless metadata.

## 5. Versioning Rules
- Stable entity IDs must not depend only on display names or labels.
- Published versions are immutable; corrections create a new version.
- Record both schema version and dataset version.
- Keep the last-known approved version available during review of a new draft.
- Define effective dates for changes that begin in the real world at a later time.
- Support rollback by selecting a previous approved release; preserve the audit trail.
- Detect merge conflicts explicitly; never silently overwrite competing edits.

## 6. Validation and QA Contract
Before a dataset can be approved:
- [ ] Required fields and types satisfy the schema.
- [ ] IDs are unique and references resolve.
- [ ] Values satisfy domain-specific constraints.
- [ ] Duplicate or conflicting records are flagged.
- [ ] Source provenance and change reason are recorded.
- [ ] Uncertainty is visible; unsupported claims are not upgraded to facts.
- [ ] Changes are compared with the previous approved version.
- [ ] High-impact changes receive human review.
- [ ] Approval is recorded separately from automated validation.
- [ ] Published output identifies the exact dataset version.

## 7. State Machine
`DRAFT → VALIDATING → IN_REVIEW → APPROVED → PUBLISHED → SUPERSEDED`

Alternative outcomes: `REJECTED`, `NEEDS_CHANGES`, `WITHDRAWN`.

A validation pass does not automatically mean approval. Approval does not automatically mean publication. Publication does not prove downstream consumers have refreshed successfully; that requires separate delivery evidence.

## 8. Roles and Separation of Duties
- **Contributor:** proposes changes and supplies evidence.
- **Validator:** runs schema and consistency checks; may be automated.
- **Reviewer:** checks domain meaning, provenance, and conflicts.
- **Approver:** authorizes canonical promotion.
- **Publisher:** releases the approved immutable version.
- **Consumer:** records which version it has ingested.

For low-risk datasets, roles may be combined under an explicit policy. High-impact or safety-relevant data should use stronger separation and independent review.

## 9. Distribution Contract
Every export or API response should expose, as appropriate:
- dataset ID and dataset version;
- schema version;
- publication timestamp and effective date;
- source / verification status;
- changelog or release notes;
- deprecation and rollback notices.

Consumers should be able to pin a version, check for updates, and identify stale cached data. A central API is a delivery mechanism; it does not substitute for data governance.

## 10. Evidence Contract
For each material change, retain:
- what changed;
- who or what proposed it;
- source/evidence references;
- validation checks and outcomes;
- reviewer and approver decisions;
- published version ID;
- distribution/consumer confirmation where required.

Do not fabricate evidence. If a check was not run, mark it `NOT RUN`. If a claim is unsupported, mark it `UNVERIFIED`.

## 11. Reuse Mapping for KMH
- **Character Bible / Master Reference:** stable character IDs, approved appearance and voice references, revision history, explicit approval.
- **Prompt Library:** prompt version, intended model/tool, input/output expectations, test evidence, and approval status.
- **Production Memory:** store validated lessons only after evidence and required human approval; link lessons to the source run and asset.
- **Case Studies / Research:** preserve original source separately from technical refinement and KMH conclusions.
- **QA Rules:** versioned criteria with expected vs actual results and failure/rework path.
- **External datasets:** source provenance, license/attribution, freshness, and confidence labels.

## 12. Implementation Phases
### Phase A — Minimum Viable Governance
1. Adopt a shared metadata contract.
2. Define per-dataset schemas and validation checks.
3. Establish draft/review/approved/published states.
4. Store immutable version snapshots and changelogs.
5. Record approval and evidence references.

### Phase B — Automation
1. Automate schema validation and diff generation.
2. Add duplicate/conflict detection.
3. Generate release notes and versioned exports.
4. Notify consumers when approved versions change.

### Phase C — Central Hub
1. Add authenticated contribution and review workflows where needed.
2. Expose versioned API and downloadable snapshots.
3. Add access control, audit logs, backups, monitoring, and rollback drills.
4. Track consumer adoption and stale-version alerts.

## 13. Acceptance Gate
A dataset is **GOVERNED** only when its schema, lifecycle, ownership, review/approval rules, version history, and evidence policy are defined.
A dataset is **IMPLEMENTED** only when the controls exist in code/configuration and are inspectable.
A dataset is **RUNTIME VERIFIED** only when actual operations have been executed and their evidence inspected.
A dataset is **OPERATIONAL** only after the relevant acceptance gate passes and an authorized owner promotes it.

## 14. Immediate Next Action
Apply this blueprint first to one bounded KMH dataset rather than expanding the architecture further. Recommended pilot: **Prompt Library Versioning + QA**, because a small controlled pilot can exercise IDs, versions, validation, approval, changelog, and evidence without changing the separate KMH-RUN-001 runtime gate.

**Current truth:** This blueprint is documentation. No implementation or runtime verification is claimed by this document.
