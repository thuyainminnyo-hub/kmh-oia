# P15 → Stage 14 Evidence Mapping Matrix

## Status
**Proposed mapping policy — implementation pending explicit approval.**

This matrix makes the bridge boundary explicit. It does not claim that P15 evidence is itself production evidence, and it does not authorize production execution.

## Identity

| Bridge input | Stage 14 target | Policy |
|---|---|---|
| explicit release_id | release | Required exact identity reference |
| explicit release→deployment mapping | deployment | Required; never inferred from identifier naming/equality |

## Direct mappings

| P15 category | Stage 14 field | Rule |
|---|---|---|
| telemetry | telemetry | Direct only when the referenced evidence is attributable and applicable |
| rollback_drill | rollback | Direct reference to the rollback drill evidence |
| incident_exercise | incident | Direct reference to the incident exercise evidence |

## Conditional / non-direct mappings

| P15 category | Possible Stage 14 fields | Rule |
|---|---|---|
| performance | stability, slo_reliability | MUST NOT satisfy either field automatically; explicit applicability/reference required |
| authorization | security_governance, change_control | MUST NOT satisfy either field automatically; explicit authorization scope/reference required |
| rollback_drill | recovery | MUST NOT satisfy automatically; recovery evidence must be separately attributable unless explicitly defined by policy |
| incident_exercise | post_deployment_review | MUST NOT satisfy automatically; review record required |

## Stage 14 fields requiring separate evidence unless explicitly supplied

- configuration
- backup_recovery
- health
- recovery
- post_deployment_review
- any other field not explicitly mapped by an approved policy

## Bridge rules

1. EvidenceClosure.complete == true proves only that the P15 required category names are present in the supplied bundle.
2. A closure result MUST NOT manufacture missing Stage 14 evidence values.
3. Each Stage 14 field marked complete MUST have an explicit evidence reference.
4. A single P15 artifact MAY support multiple Stage 14 fields only when the evidence reference and approved applicability policy explicitly support each field.
5. Missing, ambiguous, or unsupported mappings MUST block the bridge.
6. production_boundary_acknowledged remains an independent boolean and MUST be supplied explicitly.
7. Stage15Handoff.ready remains a repository-level handoff state, not production certification.

## Implementation consequence

The adapter should accept explicit mapping/reference inputs rather than inventing a 14-field package from the five P15 category names. Focused tests must prove that unsupported mappings block rather than silently pass.

## Evidence boundary

Repository code, tests, and CI validate implementation behavior only. They do not generate live telemetry, execute rollback or incident exercises, provide human authorization, or establish production readiness.
