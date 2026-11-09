# KMH-BAL-001 Geometry Refinement Specification v1

Status: DESIGN-READY SPECIFICATION; production geometry refinement not yet executed.

## 1. Objective
Define a controllable, non-destructive geometry workflow for the balloon body before detailed artwork/UV work. Keep all dimensions evidence-linked and avoid inventing physical proportions.

## 2. Asset boundaries
- `KMH-BAL-001-BODY`: main balloon shell.
- `KMH-BAL-001-SKIRT`: lower radial/ornamental fabric region; keep as a separate mesh region/object until seam and construction evidence confirms whether it is a separate physical panel.
- `KMH-BAL-001-ART-*`: material/UV zones only; not separate physical geometry unless a real seam or raised feature is evidenced.
- `KMH-BAL-001-ATT-001`: ယမ်းခွေ (Yan-Khwe), separate suspended reference asset; excluded from balloon body mesh.

## 3. Geometry zones
| Zone | Geometry intent | Evidence status |
|---|---|---|
| G01 Main envelope | Smooth inflated body with a controlled profile | Provisional silhouette only |
| G02 Crown / top | Rounded upper closure; avoid assuming exact cap shape | More views required |
| G03 Shoulder | Transition from upper dome to widest body region | Estimate from references only |
| G04 Maximum body | Main width/depth envelope | Width/depth unmeasured |
| G05 Lower taper | Controlled transition toward lower opening/skirt | Reference visible; dimensions unknown |
| G06 Lower radial skirt | Radial/petal visual structure; separate region for editability | Reference visible; exact panel construction unknown |
| G07 Attachment interface | Neutral placeholder locator only; no structural or pyrotechnic design | Position/geometry unverified |

## 4. Parameter registry
| Parameter | Value | Classification |
|---|---:|---|
| `height_m` | 7.62 | User-confirmed measurement; independent corroboration pending |
| `max_width_m` | null | Unknown; must be measured |
| `max_depth_m` | null | Unknown; must be measured |
| `profile_radii` | null | To be estimated from multi-view evidence then validated |
| `crown_curvature` | null | Unknown |
| `lower_taper_ratio` | null | Unknown |
| `skirt_radial_count` | null | Do not infer from screenshots alone |
| `mesh_resolution` | configurable | Technical parameter, not physical fact |

## 5. Modeling method
1. Preserve the existing provisional mesh as an immutable baseline.
2. Establish object axes: Z up; front direction aligned to the Buddha-facing reference after orientation confirmation.
3. Build the shell from a versioned profile curve / ring radii table; store all profile values in a parameter file.
4. Keep crown, shoulder, maximum body, lower taper and skirt as separately addressable regions.
5. Use non-destructive modifiers and named collections; avoid applying destructive operations until review.
6. Keep scale calibration as a separate operation; do not bake the user-confirmed 7.62 m height into unknown width/depth assumptions.
7. Export review meshes to GLB/OBJ/PLY and record software version, parameters, source hashes and output hashes.

## 6. Geometry QA
- Silhouette comparison from front, side and rear views.
- Cross-section checks at crown, shoulder, maximum body and lower taper.
- Watertightness, winding, connected components and non-manifold edge checks.
- Normal orientation and self-intersection checks.
- Compare against COLMAP reconstruction when a calibrated overlapping capture set exists.
- Report geometric deviations; do not assign a PASS threshold until measurement uncertainty and capture quality are known.

## 7. Do not model from unsupported assumptions
- Do not infer exact width, depth, circumference or volume from the 7.62 m height alone.
- Do not infer internal construction from the 2019 ယမ်းခွေ video.
- Do not merge ယမ်းခွေ into the shell mesh or design its pyrotechnic construction/operation.
- Do not treat screenshots as calibrated photogrammetry images.

## 8. Exit criteria
- Required measurements and view orientation recorded.
- Parameterized shell profile reviewed against reference views.
- Lower skirt region independently editable.
- Geometry QA report and artifact hashes saved.
- Human review before detailed texture production or production promotion.

Prepared != Executed != Verified != Approved.