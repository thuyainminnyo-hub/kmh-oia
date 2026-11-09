# KMH_BAL_001 — UV Mapping Readiness Gate v1.0

**Decision: NOT READY FOR FINAL UV MAPPING.**

This gate prevents UV and texture work being applied to provisional geometry or source photographs whose visual state is unknown.

## Direct inspection of preserved Geometry v1
Both local GLB assets were inspected programmatically:
- Body and lower-skirt meshes are watertight with consistent winding.
- Neither asset currently has a UV-coordinate array.
- Neither asset has a material assignment.
- Both use normalized arbitrary units; no physical scale has been applied.

This is an asset/topology inspection only. It does not certify likeness, physical dimensions, or surface accuracy.

## Readiness matrix

| Gate | Status | Evidence / blocker |
|---|---|---|
| Stable geometry baseline | Partial | Topology passes; physical scale and profile remain provisional |
| Visual state attribution | Blocked | Originals 16812–16814 are not proven BASE-UNLOADED or DISPLAYED-ATTACHED |
| Calibrated multi-view capture | Blocked | Existing images are not a calibrated overlapping orbit |
| Artwork source quality | Partial | Seven broad zones identified; lettering and occluded content unresolved |
| Surface seams / panel topology | Blocked | Seam positions and full-circumference continuity unknown |
| UV coordinate layer | Not present | No UV arrays in preserved GLBs |
| Texture bake / atlas | Not started | No accepted UV layer or calibrated texture model |
| Human artwork approval | Pending | Artwork atlas is a semantic zone map only |

## Recommended pipeline

### 1. Geometry and camera capture first
Use separate, state-attributed capture sets for `BASE-UNLOADED` and `DISPLAYED-ATTACHED`. Do not combine images from different states in one reconstruction. Each visible surface region should appear in multiple overlapping images, from different viewpoints, with similar illumination and preserved camera metadata.

COLMAP's official tutorial describes SfM as recovering sparse structure and camera parameters from overlapping images taken at different viewpoints, followed by MVS for dense geometry. It advises good surface texture, similar illumination, high overlap, each object visible in at least three images, and changing camera position rather than rotating in place. <https://colmap.github.io/tutorial.html>

### 2. Choose the texture route based on evidence
**Photogrammetry-derived texture:** after an accepted dense mesh and registered/undistorted camera set exist, evaluate COLMAP `mesh_texturer`. The official tutorial states that it produces a texture atlas and per-face UV coordinates from undistorted images. Its dense workflow requires image undistortion, stereo depth/normal estimation, fusion, and optional meshing before texturing. <https://colmap.github.io/tutorial.html>

**Curated heritage artwork:** for Buddha/halo, rear lettering, side narrative and radial ornament, wait until surface geometry, orientation and seam locations are approved. Use seam-aware Blender Unwrap and preserve source-linked layers. Blender's UV operator reference describes Smart UV Project as angle-based splitting; the angle threshold trades island count against distortion. It is presented as useful for objects such as mechanical parts or architecture, so it should not be blindly selected for continuous painted heritage artwork. <https://docs.blender.org/manual/en/4.5/modeling/meshes/editing/uv.html>

### 3. Separate artwork layers
Retain these independent zones:
- Crown rim / upper edge.
- Upper gradient / surface field.
- Front Buddha and halo.
- Side narrative.
- Rear lettering.
- Lower dark band / radial ornament.
- Surface linework.

Do not guess Burmese lettering, occluded religious artwork, physical left/right orientation, or full-wrap repeat patterns.

## Required gates before UV creation
1. Confirm each source image's visual state and subject attribution.
2. Acquire calibrated, sharp, overlapping captures with view diversity and camera metadata.
3. Record a known scale reference and independent measurement provenance.
4. Validate accepted geometry and surface coverage.
5. Confirm panel seams, boundaries and artwork continuity.
6. Obtain human approval for religious imagery, lettering, orientation, colors and layout.
7. Create a versioned UV copy; preserve Geometry v1 untouched.
8. QA UV stretch, island overlap, texel density, seam continuity, image resolution and source provenance.

## Current gate status
- UV mapping: **NOT STARTED**
- Texture baking: **NOT STARTED**
- Geometry v1: **PRESERVED**
- Geometry v2: **HOLD**
- Production: **NOT AUTHORIZED**

## Technical references
- COLMAP Tutorial: https://colmap.github.io/tutorial.html
- COLMAP FAQ (feature extraction and camera-model guidance): https://colmap.github.io/faq.html
- Blender 4.5 LTS UV Operators: https://docs.blender.org/manual/en/4.5/modeling/meshes/editing/uv.html
- Lang, Pathé & Günzel (published 27 February 2026), *From Furtwängler to Photogrammetry: A Standardized 3D Workflow for Greek Pottery*, Studies in Digital Heritage 9(2), 340–382: https://doi.org/10.14434/sdh.v9i2.41912

This gate covers non-operational digital-heritage reconstruction only.
