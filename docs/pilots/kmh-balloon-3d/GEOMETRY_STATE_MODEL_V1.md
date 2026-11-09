# KMH_BAL_001 — Geometry State Model v1.0

## Purpose
Represent the project owner's clarification that the balloon may appear in two different real-world visual states, without assuming that either prior representation is wrong.

## Two scene states

### `BASE-UNLOADED`
The base balloon envelope visual state without the separate suspended ယမ်းခွေ (Yan-Khwe).

### `DISPLAYED-ATTACHED`
The displayed visual state with the separate Yan-Khwe reference asset. The project owner reports that the envelope can appear longer in this real-world configuration. This is recorded as qualitative domain knowledge only; the amount and physical cause of any profile change have not been measured.

## Asset hierarchy
- `KMH-BAL-001-ENV`: preserved provisional balloon envelope master.
- `KMH-BAL-001-SKIRT`: separate lower-skirt visual component.
- `KMH-BAL-001-ATT-001`: separate Yan-Khwe attachment reference. No mesh is created and no design details are inferred.

Both states currently reuse the same provisional envelope master. A state-specific envelope mesh override remains empty until calibrated, state-attributed photographs and independent measurements justify it. This avoids encoding an unverified deformation into the model.

## Verified local mesh baseline
The local GLB `geometry/KMH_BAL_001_BODY_BLOCKOUT_v1.glb` was inspected:
- Bounds: approximately 1.76 × 1.76 × 1.00 normalized arbitrary units.
- Vertices: 1,282.
- Faces: 2,560.
- Watertight: yes.
- Consistent winding: yes.
- SHA-256 is recorded in `geometry_state_manifest_v1.json`.

This validates topology only. The mesh has no physical scale and is not a verified likeness.

## User-confirmed dimensions
- Overall height: 25 ft.
- Maximum body circumference: 75 ft (circumference, not diameter).
- Bottom ring diameter: 7.5 ft.
- Top ring diameter: 25 ft (diameter; do not confuse with historical AMCA Top Circle circumference).

Width, depth, crown profile, lower taper, and state-specific profile changes remain unverified.

## Geometry state rules
1. Preserve Geometry v1 unchanged.
2. Keep the envelope and Yan-Khwe as separate assets.
3. Store state selection as scene metadata, not as an invented physics simulation.
4. Do not infer a deformation magnitude or mechanism from the reported 40-viss value.
5. Do not use crop ratios from photographs as object measurements.
6. Require state attribution, calibrated views, measurement provenance, QA and human approval before a Geometry v2 proposal.

## Gates
- Two-state scene structure: **DEFINED**
- Geometry v1: **PRESERVED**
- Attached-state deformation: **REPORTED, NOT MEASURED**
- Yan-Khwe mesh: **NOT MODELED**
- Geometry v2: **HOLD**
- Production: **NOT AUTHORIZED**

This is a non-operational visual-heritage specification. It does not describe pyrotechnic construction, assembly, ignition, timing, launch, or performance.
