# KMH_BAL_001 — UV Mapping Readiness Gate v1.0

## Decision
**NOT READY FOR FINAL UV MAPPING.** The existing Geometry v1 files have no UV coordinate arrays or material assignments. The mesh topology is valid for the provisional blockout, but physical scale, profile, state attribution, panel seams and source-artwork alignment are not yet validated.

## Direct mesh inspection
Both local GLBs were inspected programmatically:
- Body and lower-skirt topology are watertight with consistent winding.
- Neither asset contains a UV coordinate array.
- Neither asset has a material assignment.
- Units remain normalized arbitrary units.

This is a direct asset inspection, not a physical accuracy or visual-likeness claim.

## Readiness matrix

| Gate | Status | Evidence / blocker |
|---|---|---|
| Stable geometry baseline | Partial | Topology passes; dimensions/profile remain provisional |
| Visual-state attribution | Blocked | 16812, 16813 and 16814 are not attributed to BASE or DISPLAYED state |
| Calibrated multi-view capture | Blocked | Existing photographs are not a calibrated overlapping orbit |
| Artwork source quality | Partial | Broad zones identified; lettering transcription and occluded details unresolved |
| Surface seams / panel topology | Blocked | Panel boundaries and full-wrap continuity unverified |
| UV coordinate layer | Not present | No UV arrays in either GLB |
| Texture bake / atlas | Not started | No validated geometry/UV base |
| Human artwork approval | Pending | Current atlas is semantic zoning only |

## Recommended mapping strategy

### A. Photogrammetry texture atlas
After state-specific calibrated capture and acceptance of dense geometry, evaluate COLMAP mesh texturing. COLMAP documents a pipeline from overlapping views through SfM camera/structure recovery and MVS dense geometry; its mesh texturer can then assign faces to suitable source images and create a texture atlas with per-face UV coordinates. The texturing stage requires the undistorted image workspace.

### B. Curated heritage artwork UV
For hand-curated artwork placement, wait for approved surface segmentation and seam locations. Use Blender's seam-aware Unwrap on accepted organic surface geometry. Do not use Smart UV Project as the default for large continuous murals or lettering: its angle-based grouping can split a surface into many islands. It may be appropriate for small isolated parts where discontinuity is acceptable.

### C. Separate artwork layers
Keep Buddha/halo, rear lettering, side narrative, lower radial ornament and surface color field as separate source-linked layers. Do not guess missing text or obscured imagery. Preserve every original image and its provenance.

## Required gates before UV creation
1. Identify the visual state of each reference: BASE-UNLOADED, DISPLAYED-ATTACHED or UNKNOWN.
2. Acquire calibrated state-specific views with high overlap, similar illumination and sufficient surface texture.
3. Preserve camera metadata and add a scale reference; record independently measured dimensions and uncertainty.
4. Confirm surface seams, panel boundaries, and full-wrap artwork continuity.
5. Validate geometry, normals and surface coverage.
6. Obtain human approval for artwork orientation, lettering, religious composition and color.
7. Generate UVs on a versioned geometry copy; preserve Geometry v1 unchanged.

COLMAP recommends textured images, similar illumination, high visual overlap, each object region visible in at least three images, and different camera viewpoints rather than rotation-only capture. The SfM stage recovers sparse structure and camera parameters; MVS densifies the reconstruction. See the technical references.

## Current gate status
- UV mapping: **NOT STARTED**
- Texture baking: **NOT STARTED**
- Geometry v1: **PRESERVED**
- Geometry v2: **HOLD**
- Production: **NOT AUTHORIZED**

## Technical references
- COLMAP Tutorial: https://colmap.github.io/tutorial
- COLMAP FAQ: https://colmap.github.io/faq.html
- Blender 5.0 UV Operators: https://docs.blender.org/manual/en/5.0/modeling/meshes/editing/uv.html
- Lang, Pathé & Günzel (2026), *From Furtwängler to Photogrammetry: A Standardized 3D Workflow for Greek Pottery*: https://scholarworks.iu.edu/journals/index.php/sdh/article/view/41912

This gate is for non-operational digital-heritage reconstruction only.
