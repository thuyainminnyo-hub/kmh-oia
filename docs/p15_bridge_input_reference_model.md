# P15 Canonical Bridge Input & Evidence Reference Model

## Status
**Proposed model — implementation pending explicit approval.**

This document defines the minimum code-level data contract for the bridge between P15 evidence closure and the existing Stage 14 operational evidence package.

## 1. Bridge input
The bridge adapter should receive an explicit input containing:
- release_id
- deployment_id
- release_deployment_mapping
- closure
- evidence_references
- stage14_mapping
- production_boundary_acknowledged

No identifier or mapping may be inferred from naming, equality, or repository conventions.

## 2. Evidence reference
Each bridged reference should preserve:
- source artifact/reference identifier
- environment
- observed timestamp
- source/operator attribution
- value/artifact reference

The reference points to supplied evidence; it does not manufacture operational evidence.

## 3. Stage 14 mapping
Each Stage 14 field must be satisfied by an explicit mapping entry:
- Stage 14 field
- P15 evidence reference(s)
- applicability / mapping rationale

A missing, ambiguous, or unsupported mapping blocks package construction.

## 4. Package construction
The adapter may construct OperationalEvidencePackage only after:
1. exact release identity is validated;
2. explicit release-to-deployment mapping is present and unambiguous;
3. P15.8 closure is complete;
4. every required Stage 14 field has an explicit evidence reference;
5. required provenance is preserved/referenced;
6. production-boundary acknowledgement is explicitly supplied.

The existing Stage 14 builder remains the completeness gate for its fourteen required fields.

## 5. Boundary
Stage15HandoffController.prepare() remains the downstream gate. Its ready state is a repository-level handoff state and does not certify production deployment, live operations, or production readiness.

## 6. Focused validation
Implementation tests should prove:
- valid explicit mapping succeeds;
- missing/ambiguous release-to-deployment mapping blocks;
- incomplete closure blocks;
- missing evidence reference/provenance blocks;
- unmapped Stage 14 fields block;
- false/missing boundary acknowledgement blocks;
- ready state retains the non-certification boundary.

Repository tests and CI validate implementation behavior only; they do not create live operational evidence.