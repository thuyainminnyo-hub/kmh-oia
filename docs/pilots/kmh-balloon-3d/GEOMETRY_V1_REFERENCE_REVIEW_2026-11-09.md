# KMH_BAL_001 — Geometry v1 Reference Review (2026-11-09)

**Review ID:** `KMH-BAL-3D-REVIEW-2026-11-09-01`  
**Status:** QUALITATIVE DISCREPANCY FLAGGED — NO GEOMETRY CHANGE

## Inputs
- `geometry/KMH_BAL_001_BODY_BLOCKOUT_v1.glb`
- `16812.jpg` — lettering-facing
- `16813.jpg` — Buddha-facing
- `16814.jpg` — side narrative

## Mesh-derived observation
The current Geometry v1 body mesh has normalized bounds approximately **1.76 × 1.76 × 1.00** (X × Y × Z), giving a height-to-maximum-planar-width ratio of approximately **0.568**. Front and side projections are identical because rotational symmetry is built into the mesh. These are normalized arbitrary units, not physical measurements.

## Qualitative reference check
The supplied perspective photographs visually suggest a taller/narrower envelope than the current blockout. This is a qualitative visual observation only. No numeric reference-image height/width ratio has been measured.

## Correction note
The earlier comparison draft displayed ratios calculated from manually selected crop-window dimensions. Those were crop aspect ratios, **not balloon silhouette measurements**, and must not be used as reference geometry metrics. This corrected review removes that comparison.

## Limitations
- Perspective, camera pitch, inflation state, ground support, occlusion, lens distortion and crop can alter apparent proportions.
- The reference set is not a calibrated overlapping photogrammetry dataset.
- No true physical width, depth or physical height/width ratio is inferred from these photographs.
- This review is not an authorization to modify the mesh.

## Gate decision
- Existing topology QA: PASS (topology only).
- Visual similarity: NOT VALIDATED; qualitative discrepancy flagged.
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

![Corrected Geometry v1 reference review](../evidence/geometry_v1_reference_review_2026-11-09.png)
