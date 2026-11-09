# KMH_BAL_001 — Image Metadata & Capture Quality Audit v1.0

## Decision
**Metadata audit complete; calibrated photogrammetry remains NOT READY.**

## Inventory summary
- Files reviewed: 16.
- Missing files: 0.
- EXIF present: 0.
- Camera model available: 0.
- Original capture timestamp available: 0.
- Exact byte-identical duplicate groups by SHA-256: 0.
- Distinct image dimensions: 2.

### Dimensions observed
- 16812–16814: 1152 × 2048 px.
- 16822–16850: 1845 × 2048 px.

Image resolution and EXIF are descriptive metadata. Neither proves calibration or photogrammetry readiness. The absence of EXIF means the supplied files do not retain camera/lens/timestamp evidence in their current form; it does not by itself prove the images are visually poor.

## Source group interpretation
- 16812–16814: original artwork-facing photos; qualitative artwork and visual identity references.
- 16822/16824: close-up Yan-Khwe detail screenshots; not proof of a complete displayed/attached balloon state.
- 16826–16842: video-frame screenshots from one sequence; not independent calibrated camera captures.
- 16844: ground-laid artwork panel; artwork reference only.
- 16850: photographed competition rules page; separate document-evidence track.

## Duplicate screening correction
An exploratory 8×8 average-hash screen produced too many candidate near-duplicate pairs across visually different, similarly framed vertical images. That screen is **withdrawn as unreliable** and its pair flags are not used as evidence. Exact SHA-256 comparison found no byte-identical duplicate files. The video screenshots remain known to come from a shared video sequence based on their source grouping, not from perceptual-hash inference.

## Readiness findings
- State attribution: unresolved for all balloon/attachment images.
- Camera model/focal-length/time metadata: absent from all 16 files.
- Calibration: not established.
- Scale reference: absent from existing sources.
- Viewpoint overlap/parallax: not documented as a calibrated capture sequence.
- Photogrammetry: not ready.
- Geometry v1: preserve.
- Geometry v2: HOLD.
- COLMAP: blocked pending a state-attributed capture set and human QA.

## Required next evidence
1. A source-confirmed `BASE-UNLOADED` or `DISPLAYED-ATTACHED` capture set.
2. Original camera files with EXIF, or a separately documented camera calibration record.
3. A safe, independently measured scale reference or an explicitly unscaled reconstruction plan.
4. Multiple distinct viewpoints with overlapping visual content.
5. A human-reviewed capture manifest.

## Scope
This audit checks file integrity, dimensions, EXIF presence and exact duplicate identity. It does not establish physical dimensions, balloon state, camera calibration, lens distortion, 3D geometry or artwork UV coordinates.
