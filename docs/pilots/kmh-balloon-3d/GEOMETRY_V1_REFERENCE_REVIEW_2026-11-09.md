# KMH_BAL_001 — Geometry v1 Reference Review (2026-11-09)

**Review ID:** `KMH-BAL-3D-REVIEW-2026-11-09-01`  
**Status:** STATE DIFFERENCE REPORTED — NO GEOMETRY CHANGE

## Inputs
- `geometry/KMH_BAL_001_BODY_BLOCKOUT_v1.glb`
- `16812.jpg` — lettering-facing
- `16813.jpg` — Buddha-facing
- `16814.jpg` — side narrative

## Mesh-derived observation
The current Geometry v1 body mesh has normalized bounds approximately **1.76 × 1.76 × 1.00** (X × Y × Z), giving a height-to-maximum-planar-width ratio of approximately **0.568**. Front and side projections are identical because rotational symmetry is built into the mesh. These are normalized arbitrary units, not physical measurements.

## New user-provided domain clarification — unloaded vs displayed/loaded state
The project owner clarified that the two appearances may both be correct because, in the real-world configuration, attaching the reported 40-viss ယမ်းခွေ (Yan-Khwe) can make the balloon's visible body/profile appear longer.

Record the following distinct visual states:
1. **BASE / UNLOADED REFERENCE STATE** — envelope appearance without the suspended Yan-Khwe attachment.
2. **DISPLAYED / ATTACHED REFERENCE STATE** — appearance in the real-world display configuration with the separate Yan-Khwe attachment.

This is user-provided domain knowledge. The exact deformation, structural response, and dimensional change have not been independently measured. Do not infer or calculate mechanical behavior from the reported weight.

## Revised visual comparison interpretation
The previous observation that the blockout appeared wider/shorter than the photographs must not be treated as proof that either model or photograph is wrong. A difference in physical configuration/state may explain part of the apparent silhouette difference. The state of the three reference photographs is not yet confirmed, so the visual comparison remains unresolved.

## Correction note
The earlier comparison draft displayed ratios calculated from manually selected crop-window dimensions. Those were crop aspect ratios, **not balloon silhouette measurements**, and must not be used as reference geometry metrics.

## Limitations
- Perspective, camera pitch, inflation state, physical attachment state, ground support, occlusion, lens distortion and crop can alter apparent proportions.
- The reference set is not a calibrated overlapping photogrammetry dataset.
- No actual deformation, physical width/depth, or loaded-state geometry is inferred.
- This review is not an authorization to modify the mesh or model the attachment mechanics.

## Gate decision
- Existing topology QA: PASS (topology only).
- Visual similarity: STATE-DEPENDENT / NOT YET VALIDATED.
- Physical scale and state-specific profile: HOLD.
- Geometry v2: HOLD pending calibrated images of clearly identified states and independent envelope measurements.
- Production: NOT AUTHORIZED.
- Geometry v1: PRESERVE unchanged as a baseline.

## Required evidence
1. Identify whether each reference image depicts BASE / UNLOADED or DISPLAYED / ATTACHED state.
2. Obtain comparable, calibrated images of the same balloon in clearly recorded states, where safely and lawfully available.
3. Record independent envelope dimensions and measurement provenance for each documented state.
4. Keep the balloon envelope and suspended Yan-Khwe as separate visual assets.
5. Do not infer hidden structure or operational attachment design from photographs.

