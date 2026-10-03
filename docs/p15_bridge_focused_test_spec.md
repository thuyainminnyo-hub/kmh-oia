# P15 Canonical Bridge — Focused Test Specification

## Status
**Proposed test specification — implementation pending explicit bridge approval.**

## Purpose
Lock the deterministic validation boundary before bridge code is written. These tests validate repository-level contract behavior only.

## Test matrix

| ID | Scenario | Expected |
|---|---|---|
| BR-01 | Complete P15 closure + explicit release→deployment mapping + all 14 Stage14 references + valid provenance + boundary acknowledgement | Bridge constructs complete OperationalEvidencePackage |
| BR-02 | Missing release→deployment mapping | Block |
| BR-03 | Ambiguous release→deployment mapping | Block |
| BR-04 | P15 closure release_id differs from requested release_id | Block |
| BR-05 | P15.8 closure incomplete | Block |
| BR-06 | Stage14 field has no evidence reference | Block |
| BR-07 | Evidence reference lacks required provenance/reference data | Block |
| BR-08 | Unsupported P15→Stage14 mapping | Block |
| BR-09 | Conditional mapping lacks explicit applicability/rationale | Block |
| BR-10 | production_boundary_acknowledged=False | Downstream handoff blocked |
| BR-11 | production_boundary_acknowledged missing/non-boolean | Reject |
| BR-12 | Complete package reaches Stage15HandoffController with explicit acknowledgement | Repository-level ready |
| BR-13 | Stage15Handoff.ready is inspected | Must not be represented as production certification |
| BR-14 | SHA-256 receipt matches supplied bytes | Integrity verification passes only; no operational-validity claim |
| BR-15 | SHA-256 receipt mismatches supplied bytes | Integrity verification fails |

## Invariants
1. release_id and deployment_id remain distinct.
2. Release→deployment mapping is explicit; no equality/name inference.
3. EvidenceClosure.complete does not manufacture Stage14 evidence.
4. Every Stage14 complete field has an explicit reference.
5. Provenance is preserved/referenced.
6. Unsupported or ambiguous mappings block.
7. Boundary acknowledgement is independent of evidence completeness.
8. Repository tests/CI do not constitute live operational evidence.

## Implementation boundary
No bridge source code is added by this specification. After explicit approval, implementation should be the smallest adapter required to satisfy the contract and this test matrix, followed by exact-head CI verification.

## Evidence boundary
Passing repository tests demonstrates deterministic implementation behavior only. It does not establish live telemetry, rollback execution, incident exercise results, human authorization, production deployment, or production readiness.
