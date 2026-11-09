# KMH_BAL_001 — 3D Reconstruction Restart Plan v1.0

## Decision
Resume the original objective: non-operational 3D heritage reconstruction of the Myanmar traditional balloon envelope and its artwork. Pyrotechnic operational research remains deferred and outside this workstream.

## Preserve existing assets
- Geometry v1 provisional body and lower-skirt blockout.
- Geometry Evidence Matrix v1.0.
- Team Design Identity Registry v1.0.
- Unified Evidence Registry v1.0.
- Existing capture preflight, geometry refinement, measurement calibration, and UV mapping specifications.

Do not replace, rescale, or reshape Geometry v1 on assumptions alone.

## Project dimensions and uncertainty
- Overall height: 25 ft / 7.62 m — user-confirmed; independent measurement method/tolerance still pending.
- Maximum body circumference: 75 ft — user-confirmed; preserve as circumference, not diameter.
- Bottom ring diameter: 7.5 ft — user-confirmed.
- Top ring diameter: 25 ft — user-confirmed.
- Width/depth, crown curvature, lower taper, maximum-body station and radial panel count: unverified.
- The historical AMCA Top Circle value of 25 ft is a circumference claim; do not conflate it with the user's 25 ft top-ring diameter.

## Workstreams

### 3D-01 — Reference audit
Inventory source images, record source/date/team attribution, classify each view, and label limitations. Screenshots sampled from one video are not independent calibrated viewpoints. Ground-laid artwork references are not proof of ring dimensions.

### 3D-02 — New capture set
Acquire a new, attributable capture set of one stable physical balloon configuration:
- Front, rear, left, right, upper, lower, and overlapping oblique views.
- Ensure each visible surface region appears in at least three useful images.
- Move the camera between viewpoints to create parallax; rotation-only panoramas are not sufficient for SfM.
- Keep illumination reasonably consistent, avoid motion blur and strong specular highlights, and preserve original image files and EXIF metadata.
- Record camera/device, lens/focal length, image dimensions, capture order, date, lighting, configuration state, operator and source permissions.
- Include a known scale reference or measured control distance. Record measurement method, endpoints, instrument, operator and uncertainty.

COLMAP's official tutorial recommends textured images, similar illumination, high image overlap, seeing each object region in at least three images, and changing camera viewpoints. It also describes the pipeline as Structure-from-Motion (sparse model and camera poses) followed by Multi-View Stereo (dense point cloud and optional mesh/texture).

### 3D-03 — Reconstruction comparison
Keep two evidence streams separate:
1. COLMAP SfM/MVS reconstruction.
2. Tripo multiview output, only after image-set validation and explicit approval for any paid API generation.

Compare the outputs only after independent scale and coordinate alignment. Record camera coverage, registered-image ratio, sparse/dense completeness, holes, silhouette deviation and measurement residuals. Do not treat AI-generated geometry as measurement truth.

### 3D-04 — Geometry refinement
Preserve Geometry v1 as a baseline. Refine only when calibrated views and independent measurements support a specific change. Maintain separate body and lower-skirt components. Do not infer width/depth from height or assume rotational symmetry.

### 3D-05 — Artwork and UV mapping
Keep geometry separate from front/rear/side artwork. Preserve source images unchanged; maintain provenance for Buddha imagery, lettering, colors and ornaments. AI-recreated lettering or religious artwork must never be represented as original source artwork. Validate seam continuity, UV stretching, orientation and visual fidelity.

### 3D-06 — QA and release
Run mesh integrity, topology, normals, connected-component, dimension, silhouette, texture and provenance checks. Record tool versions, input hashes, output hashes and QA evidence. Require human review before merging and any production promotion.

## General photogrammetry research references
- COLMAP Tutorial: https://colmap.github.io/tutorial.html
- PIX4D image acquisition best practices: https://support.pix4d.com/hc/best-practices-for-image-acquisition-and-photogrammetry
- Nazim et al. (2025), “Methodology of Object Reconstruction by Photogrammetry and Structured-Light Scanning for Industrial 3D Visualisation,” Sensors 25(23), 7177: https://pmc.ncbi.nlm.nih.gov/articles/PMC12693997/

## Gates at restart
- Geometry v1: PRESERVED.
- Existing supplied images: useful for semantic artwork and qualitative silhouette review; not sufficient for calibrated photogrammetry.
- New calibrated capture set: REQUIRED.
- Geometry v2: HOLD pending measurement/capture evidence and human approval.
- Artwork mapping: may proceed as a provenance-labelled visual review, not as final UV approval.
- Production release: NOT AUTHORIZED.

## Excluded from this plan
No pyrotechnic design, weight/heat calculations, ignition, timing, assembly, launch or flight-performance optimization. The 3D scope is the non-operational envelope, heritage artwork and visual documentation only.
