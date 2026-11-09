# KMH-BAL-001 Geometry Blockout v1 — Execution Evidence

Status: EXECUTED / TOPOLOGY-VERIFIED ONLY. This is a normalized parametric blockout, not a measured reconstruction or production-ready digital twin.

## Artifacts generated
- `geometry/KMH_BAL_001_BODY_BLOCKOUT_v1.glb` — main balloon body blockout.
- `geometry/KMH_BAL_001_LOWER_SKIRT_BLOCKOUT_v1.glb` — separate lower-skirt blockout.
- `scripts/build_parametric_blockout_v1.py` — reproducible generator.
- `evidence/geometry_blockout_v1_qa.json` — QA report.
- `evidence/geometry_blockout_v1_checksums.sha256` — SHA-256 checksums.

## Geometry QA
| Mesh | Vertices | Faces | Watertight | Winding | Units |
|---|---:|---:|---|---|---|
| Body | 1,282 | 2,560 | PASS | PASS | Normalized arbitrary |
| Lower skirt | 514 | 1,024 | PASS | PASS | Normalized arbitrary |

Both meshes are separate, editable GLB objects. Body uses Z-up coordinates and a 128-segment lathed profile. Lower skirt is a separate visual placeholder and is not fused to the body.

## Critical limitations
- Profile stations and radii are provisional design parameters, not measurements extracted from photographs.
- The 25 ft / 7.62 m user-confirmed height has not been used to scale the mesh because width/depth/profile are not measured.
- No UVs, artwork textures, Blender `.blend` master, Tripo generation, or COLMAP reconstruction are included.
- No internal balloon structure or ယမ်းခွေ geometry is included.
- Topology PASS does not imply silhouette fidelity, scale accuracy, engineering validity, or production approval.

## Next gate
Obtain calibrated capture/measurements; revise profile parameters from evidence; compare silhouette and cross-sections; then proceed to artwork UV work. Human review remains required before production promotion.