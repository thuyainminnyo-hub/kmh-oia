# P15 Canonical Evidence → Stage 15 Handoff Bridge Contract

## Status
**Proposed contract — implementation pending explicit approval.**

This document defines the contract boundary between P15.8 evidence closure and the existing Stage 14 operational evidence package / P14.20 Stage 15 handoff. It does not itself create operational evidence or authorize production execution.

## Canonical flow

`P15.9 EvidenceReceiptManifest → P15.7 EvidenceBundle → P15.8 EvidenceClosure → Bridge Adapter → OperationalEvidencePackage → Stage15HandoffController`

## Contract

### 1. Identity
- `release_id` and `deployment_id` are distinct identifiers.
- The adapter MUST receive an explicit release-to-deployment mapping reference.
- The adapter MUST reject missing or ambiguous mappings.
- Identifier equality or naming convention MUST NOT be inferred as a mapping.

### 2. Evidence completeness
- `EvidenceClosure.complete` is a closure result over supplied evidence categories.
- Closure status MUST NOT be treated as independent proof of authenticity or live operational validity.
- The adapter MUST preserve or reference the underlying attributable evidence; it MUST NOT fabricate evidence values.

### 3. Provenance
For every bridged evidence reference, preserve or reference:
- environment
- observed timestamp
- source / operator attribution
- artifact or value reference

### 4. Category mapping
The P15 required categories are:
- `telemetry`
- `performance`
- `rollback_drill`
- `authorization`
- `incident_exercise`

The Stage 14 package requires fourteen categories:
`release`, `deployment`, `configuration`, `backup_recovery`, `security_governance`, `health`, `telemetry`, `stability`, `rollback`, `recovery`, `slo_reliability`, `incident`, `change_control`, `post_deployment_review`.

A production implementation MUST define an explicit mapping policy for how supplied P15 evidence references satisfy individual Stage 14 fields. One P15 category MUST NOT silently be assumed to prove unrelated Stage 14 fields.

### 5. Boundary acknowledgement
`production_boundary_acknowledged` is a separate boolean input to `Stage15HandoffController.prepare()` and MUST NOT be inferred from evidence completeness, authorization evidence, CI status, or receipt metadata.

### 6. Certification boundary
A `Stage15Handoff` in `ready` phase means repository-level handoff prerequisites were satisfied. It MUST NOT be represented as production deployment certification, live operational readiness, or authorization to execute production changes.

## Required adapter inputs

- exact `release_id`
- explicit `deployment_id`
- release-to-deployment mapping reference
- P15.8 closure state
- underlying attributable evidence references
- explicit production-boundary acknowledgement

## Blocking conditions

The adapter MUST block when any of the following applies:
- release/deployment mapping is missing or ambiguous
- P15.8 closure is incomplete
- attributable evidence reference is missing
- a required mapping from P15 evidence to Stage 14 evidence is undefined
- production-boundary acknowledgement is absent or false

## Validation expectations

Focused tests should cover:
1. valid explicit mapping and complete evidence path
2. missing mapping
3. ambiguous mapping
4. incomplete closure
5. missing provenance/reference
6. unmapped Stage 14 requirement
7. missing boundary acknowledgement
8. explicit proof that `ready` does not become production certification

## Evidence boundary
Repository code, tests, and CI validate implementation behavior only. They do not generate live telemetry, execute rollback or incident exercises, supply human authorization, or establish production readiness.
