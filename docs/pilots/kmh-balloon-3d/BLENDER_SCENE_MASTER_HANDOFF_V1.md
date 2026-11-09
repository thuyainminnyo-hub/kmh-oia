# KMH_BAL_001 — Blender Scene Master Handoff v1.0

## Deliverable
A portable GLB review scene and a Blender-native scene builder script have been prepared.

- Portable scene: `KMH_BAL_001_TWO_STATE_REVIEW_SCENE_v1.glb`
- Body source: `KMH_BAL_001_BODY_BLOCKOUT_v1.glb`
- Lower-skirt source: `KMH_BAL_001_LOWER_SKIRT_BLOCKOUT_v1.glb`
- Blender builder: `scripts/build_blender_scene_master.py`
- Manifest: `registry/scene_master_manifest_v1.json`

The portable GLB is packaged locally with both unchanged source GLBs. The binary package is not committed to this repository; the repository tracks the specification, manifest, and builder script.

## Scene structure
- `STATE_BASE_UNLOADED`: envelope and lower skirt.
- `STATE_DISPLAYED_ATTACHED`: same envelope and lower-skirt mesh resources, plus a separate unpositioned Yan-Khwe reference node.
- Artwork layers: empty named nodes for front Buddha/halo, rear lettering, side narrative, lower radial ornament, and color/surface patterns.
- Yan-Khwe: reference-only, no mesh and no position inferred.

The two states currently reuse the same Geometry v1 meshes. The reported longer appearance in the displayed/attached state is user-provided qualitative knowledge; no deformation magnitude or mechanism is encoded. In the portable review GLB, the two state branches are placed side-by-side only for comparison. Those offsets are presentation offsets, not physical placement.

## Source asset integrity
- Body SHA-256: `1c3b57d2146686926e6d421aaf07b5382ba634a9d9df4138804fe921a20078b9`
- Lower skirt SHA-256: `ab57f9ee89dbfcedc494566f9b41809917da41e6ddd966775129f73e2a9d284b`
- Portable scene SHA-256: `c6512e9d8c33039c8c27ee1fcaa0baaa7c559e0bba44d5bccf65026d7ec2e9e8`

## Validation
- GLB exported and reloaded successfully.
- Required state, artwork-zone and attachment-reference nodes verified.
- Exactly two shared geometry resources are used (body and lower skirt).
- Mesh source hashes match the preserved v1 files.
- No physical scale is applied.
- Blender-native `.blend` was not generated in this workspace because Blender is not installed. The builder script is included for execution in a Blender installation; script syntax was checked, but Blender API execution has not been tested here.

## Gates
- Geometry v1: **PRESERVED**
- Portable GLB scene: **EXPORTED AND RELOAD-VERIFIED**
- Blender-native `.blend`: **NOT GENERATED**
- Artwork/UV mapping: **EMPTY LAYERS ONLY**
- State-specific deformation: **NOT MODELED / NOT MEASURED**
- Geometry v2: **HOLD**
- Production: **NOT AUTHORIZED**

This is a non-operational visual-heritage handoff. It does not model pyrotechnic components or operational mechanisms.
