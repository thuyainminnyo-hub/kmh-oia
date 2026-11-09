# KMH_BAL_001 — Geometry Change-Control Gate v1.0

## Purpose
Protect the preserved Geometry v1 baseline and ensure a future Geometry v2 is created only from traceable, state-specific evidence and explicit human approval.

## Locked baseline
The baseline registry records SHA-256 identity for:
- `KMH_BAL_001_BODY_BLOCKOUT_v1.glb`
- `KMH_BAL_001_LOWER_SKIRT_BLOCKOUT_v1.glb`

Geometry v1 is immutable under this gate. Any proposed edits must be made on a new versioned copy. Original assets must remain recoverable and hash-identical.

## Owner-confirmed dimensions — independent verification pending
- Overall height: 25 ft (HEIGHT).
- Maximum body circumference: 75 ft (CIRCUMFERENCE, not diameter).
- Bottom ring diameter: 7.5 ft (DIAMETER).
- Top ring diameter: 25 ft (DIAMETER).

These values retain their semantic types and are not automatically treated as calibrated constraints.

## Change-request evidence requirements
A Geometry v2 candidate must include:
1. A target visual state: `BASE-UNLOADED` or `DISPLAYED-ATTACHED`.
2. Source-backed state confirmation for the capture set.
3. Camera/calibration provenance or an explicitly unscaled reconstruction basis.
4. Scale-control and independent measurement records with method, datum/endpoints, instrument, observer, date, uncertainty and source.
5. Hashes of source images and candidate geometry assets.
6. A rationale naming observed discrepancy and affected profile features.
7. QA results for mesh integrity, dimension residuals, silhouette comparison, state consistency and provenance.
8. Recorded limitations and missing coverage.

## Independent gate logic
- Documentation or CI passing does not authorize geometry promotion.
- A user-confirmed dimension is not equivalent to an independent measurement.
- A perspective photo or crop ratio is not a measured profile.
- `UNKNOWN` state cannot be used for a state-specific Geometry v2 promotion.
- The reported longer appearance in DISPLAYED-ATTACHED state cannot be encoded as a deformation amount until measured.
- Yan-Khwe remains a separate visual reference asset; no attachment mechanics are inferred.
- Body and lower skirt remain separate assets unless an approved evidence-based decision changes that boundary.

## Required approvals
Both are required:
- Technical reviewer: APPROVED, with date and evidence reference.
- Project owner: APPROVED, with date and evidence reference.

A Geometry v2 candidate remains on HOLD if any evidence item, QA result, limitation statement or approval is missing.

## Release policy
The validator can return only `ELIGIBLE_FOR_HUMAN_RELEASE_REVIEW`; it never changes assets, approves a PR, merges, or deploys. Merge and production approval are separate decisions.

## Scope boundary
This gate covers non-operational visual heritage geometry only. It excludes pyrotechnic operating design, weight/heat calculations, ignition, timing, assembly, launch and flight-performance optimization.

## Current status
- Geometry v1: PRESERVED / HASH-LOCKED.
- Geometry v2: HOLD.
- Independent dimension verification: PENDING.
- State-attributed calibrated capture: PENDING.
- Production: NOT AUTHORIZED.
