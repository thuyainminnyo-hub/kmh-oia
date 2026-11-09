# KMH_BAL_001 — Geometry v1 Reference Review (2026-11-09)

**Review ID:** `KMH-BAL-3D-REVIEW-2026-11-09-01`  
**Status:** VISUAL DISCREPANCY FLAGGED — NO GEOMETRY CHANGE

## Inputs
- `geometry/KMH_BAL_001_BODY_BLOCKOUT_v1.glb`
- `16812.jpg` — lettering-facing
- `16813.jpg` — Buddha-facing
- `16814.jpg` — side narrative

## Mesh-derived observation
The current Geometry v1 body mesh has normalized bounds approximately **1.76 × 1.76 × 1.00** (X × Y × Z), giving a height-to-maximum-planar-width ratio of approximately **0.568**. Front and side projections are identical because rotational symmetry is built into the mesh.

## Qualitative reference check
Approximate image-frame height/width ratios, from manually estimated balloon bounding boxes:
- 16812: 1.243
- 16813: 1.319
- 16814: 1.250

These are rough image-frame estimates from perspective photographs, not calibrated object measurements.

**Finding:** Geometry v1 appears substantially wider/shorter than the supplied balloon reference photographs. This is a significant visual discrepancy signal. The current blockout must not be described as a visually matched reconstruction.

## Limitations
- Perspective, camera pitch, inflation state, ground support, occlusion and image crop can alter apparent proportions.
- The reference set is not a calibrated overlapping photogrammetry dataset.
- No true physical width, depth or physical height/width ratio is inferred from these photographs.
- This review is not an authorization to modify the mesh.

## Gate decision
- Existing topology QA: PASS (topology only).
- Visual similarity: NOT VALIDATED; discrepancy flagged.
- Physical scale: HOLD.
- Geometry v2: HOLD pending calibrated captures and independent measurements.
- Production: NOT AUTHORIZED.
- Geometry v1: PRESERVE unchanged as a baseline.

## Required evidence
1. Calibrated front and side captures of the same stable balloon state.
2. Scale reference and measurement provenance.
3. Independently measured maximum width and depth.
4. Crown profile and lower taper measurements.
5. Confirmed image orientation and subject identity.

