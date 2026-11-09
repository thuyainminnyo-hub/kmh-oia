# KMH_BAL_001 — State-aware Geometry Measurement & Profile Register v1.0

## Purpose
Prepare consistent, evidence-backed geometry measurements for the balloon's two visual states. This is non-operational geometry documentation only.

## Preserve owner-confirmed dimensions and their meanings

| Feature | Owner-confirmed value | Semantic type | Independent measurement |
|---|---:|---|---|
| Overall envelope height | 25 ft | Height | Pending |
| Maximum body circumference | 75 ft | Circumference, not diameter | Pending |
| Bottom ring | 7.5 ft | Diameter | Pending |
| Top ring | 25 ft | Diameter | Pending |

Do not conflate the owner's 25 ft top-ring diameter with historical references that report a 25 ft top-circle circumference. Keep each source and semantic type attached to its value.

## State separation
- `BASE-UNLOADED`
- `DISPLAYED-ATTACHED`
- `UNKNOWN`

Each measurement session must represent one confirmed state. Do not compare profile values across states unless state provenance is adequate. The owner's observation that the displayed/attached appearance can look longer is retained as qualitative domain knowledge; this register does not calculate or infer the cause or amount of that change.

## Named profile stations
1. `PROFILE-01 — CROWN_UPPER_ENVELOPE`
2. `PROFILE-02 — UPPER_SHOULDER`
3. `PROFILE-03 — MAXIMUM_BODY_REGION`
4. `PROFILE-04 — LOWER_TAPER`
5. `PROFILE-05 — BOTTOM_RING_REFERENCE`

These are location labels only. They do not prescribe operational procedures or imply exact station heights. Record where a station is defined on the source object.

Where supported by an authorized measurement record, record width, depth, explicitly measured circumference, or vertical position from a stated datum. Never infer width/depth from height or perspective photographs.

## Provenance required for every numeric measurement
- state and subject identity;
- feature definition, units, datum/endpoints;
- method and instrument;
- observer and date;
- uncertainty/tolerance;
- source evidence;
- independent verification status;
- reviewer and review decision.

A numeric value without provenance remains an unverified claim, not a geometry constraint.

## Safety boundary
Use existing authorized measurement records or measurements made by qualified personnel under the responsible site/event safety authority. This protocol does not authorize approaching, touching, climbing on, moving, loading, unloading, suspending or altering the balloon or attached components. If a measurement cannot be obtained safely and permissibly, mark it unavailable.

## Geometry update gate
- Geometry v1: PRESERVE.
- Geometry v2: HOLD until state attribution, independent measurements, provenance, QA and human approval exist.
- Keep envelope, lower skirt and Yan-Khwe as separate visual assets.
- Only propose a state-specific profile override when repeatable, state-attributed evidence supports it.

## Current status
Four owner-confirmed dimension records are preserved; independent measurement records have not been added by this template. State-specific profile evidence is pending. Geometry v1 remains preserved, Geometry v2 remains HOLD, and production is not authorized.
