# KMH-BAL-001 Capture & API Preflight Specification v1

Status: PREPARED — no capture or paid generation is implied by this document.

## Purpose
Define the minimum evidence and validation gates before running Tripo H3.1 multiview generation or COLMAP reconstruction for the KMH Myanmar balloon pilot.

## Asset facts
- Asset ID: `KMH-BAL-001`.
- Three original reference photos are available: Buddha-facing, side artwork, rear lettering.
- The current three-photo set is not a calibrated overlapping 360-degree dataset.
- Height: 25 ft / 7.62 m, user-confirmed. Independent corroboration and measurement method/tolerance remain pending.
- Width and depth: unknown.
- Provisional mesh topology was checked, but likeness, dimensions, and artwork fidelity are not established.

## Capture protocol
- Pilot target: approximately 40–80 images, adjusted to actual coverage and quality; this is a project target, not a COLMAP requirement.
- Capture distinct front, left, right, rear, upper, lower, and detail coverage.
- Move the camera to different viewpoints; do not rely on rotation from one fixed location.
- Ensure strong overlap and that each surface region appears in at least three usable images.
- Keep lighting and balloon configuration stable. Separate visibly different inflation/deformation states.
- Preserve camera originals and EXIF. Never overwrite original files with processed versions.
- Record operator, timestamp, camera/lens, focal length, exposure, lighting, viewpoint sequence, and balloon state.
- Create a SHA-256 manifest with filename, dimensions, MIME type, EXIF availability, capture group, and sequence number.

## Physical measurement evidence
- Record height measurement method, date, operator, endpoints, instrument, and uncertainty/tolerance.
- Measure maximum width and depth independently; do not infer them from height.
- Confirm the measurement refers to the same balloon configuration as the capture dataset.

## Tripo preflight
- Endpoint: `POST https://openapi.tripo3d.ai/v3/generation/multiview-to-model`.
- Model: `v3.1-20260211`.
- Use one input representation per request; do not mix view-key, legacy positional, and prior task ID forms.
- Front view is required and at least two valid views are required. A complete four-side view set is preferred for the pilot.
- Validate view orientation before labeling left/right.
- For `generate_parts=true`, explicitly set `texture=false` and `pbr=false`; do not combine with `quad` or `smart_low_poly`.
- Keep API keys in a secret manager or environment variable. Never commit keys or paste them into chat.
- Obtain explicit approval of expected credits before paid generation.
- Preserve exact request, model version, seeds, task ID, response, output URL, artifact SHA-256, and credit usage.
- Do not treat `auto_size` as proof of exact 7.62 m height; measure exported bounds and calibrate separately.

## COLMAP plan
- Start with SIFT on a validated, well-overlapped, consistently lit capture set.
- If diagnostics justify ALIKED, run it in a separate database/workspace; never mix SIFT and ALIKED descriptors in one database.
- Preserve sparse model, camera poses, dense point cloud, mesh, and texture outputs as separate versioned artifacts.

## QA gates
1. Input integrity: immutable originals and verified SHA-256 manifest.
2. Capture quality: view coverage, overlap, sharpness, exposure, stable object state.
3. Geometry: mesh validity and comparison against independent reconstruction.
4. Scale: measured 7.62 m height reference with documented method/tolerance; width/depth separately measured.
5. Artwork: original-reference comparison, UV distortion and texture coverage review.
6. Governance: independent QA and explicit human approval before production promotion.

## Current blockers
- Calibrated overlapping capture dataset not yet available.
- Side-artwork physical orientation not yet confirmed.
- Width/depth and measurement method/tolerance not recorded.
- Tripo execution, COLMAP reconstruction, and Blender editable master are not verified.

## Release rule
Prepared != Executed != Verified != Approved. This pilot must remain isolated from the production runtime until all required gates pass and a human explicitly approves promotion.