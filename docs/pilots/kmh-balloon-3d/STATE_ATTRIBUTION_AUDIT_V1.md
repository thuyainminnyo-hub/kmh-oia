# KMH_BAL_001 — Existing Reference State Attribution Audit v1.0

## Decision
**No existing image conclusively establishes the balloon's BASE-UNLOADED or DISPLAYED-ATTACHED state.** Preserve state as `UNKNOWN` unless direct source confirmation or an unobstructed visual cue establishes it.

## Audit totals
- Supplied image files reviewed: 16.
- Confirmed BASE-UNLOADED: 0.
- Confirmed DISPLAYED-ATTACHED: 0.
- UNKNOWN: 14.
- NOT_APPLICABLE: 2.
- Calibrated photogrammetry-ready: 0.

## Important findings
- `16822.jpg` and `16824.jpg` show close-up views of the separate Yan-Khwe visual asset in a 2019 video. These frames do not show the balloon envelope or its connection to the attachment. They are attachment-detail references, not proof of the complete DISPLAYED-ATTACHED state.
- `16812.jpg`, `16813.jpg` and `16814.jpg` show balloon artwork views, but the lower attachment area is partly occluded and source provenance does not identify the state.
- `16826.jpg` through `16842.jpg` are screenshots sampled from one social video sequence. They are not nine independent calibrated camera captures. The envelope is visible, but people/cropping obscure the lower area, so the attachment state cannot be established.
- `16844.jpg` shows a ground-laid decorative radial panel. It does not establish balloon state or bottom-ring dimensions.
- `16850.jpg` is a photograph of a competition-rules document and belongs to the document-evidence track.

## Complete image-by-image register

| File | Source class | Visual role | State | Reason |
|---|---|---|---|---|
| 16812 | Original photo | Rear / lettering-facing | UNKNOWN | Lower attachment area partly occluded |
| 16813 | Original photo | Front / Buddha-facing | UNKNOWN | Lower attachment condition not established |
| 16814 | Original photo | Side narrative-facing | UNKNOWN | Lower attachment condition not established |
| 16822 | 2019 video screenshot | Yan-Khwe detail | UNKNOWN | Balloon-to-attachment connection not visible |
| 16824 | 2019 video screenshot | Yan-Khwe detail | UNKNOWN | Balloon envelope not visible |
| 16826 | Social video screenshot | Front / oblique artwork | UNKNOWN | Base cropped/occluded |
| 16828 | Social video screenshot | Lettering-facing | UNKNOWN | Base cropped/occluded |
| 16830 | Social video screenshot | Buddha / oblique | UNKNOWN | Base cropped/occluded |
| 16832 | Social video screenshot | Side narrative / oblique | UNKNOWN | Single video frame; attachment status not established |
| 16834 | Social video screenshot | Buddha-facing | UNKNOWN | People and crop obscure lower attachment region |
| 16836 | Social video screenshot | Side / rear oblique | UNKNOWN | Lower region occluded |
| 16838 | Social video screenshot | Side / rear oblique | UNKNOWN | Same source video; not an independent capture |
| 16840 | Social video screenshot | Lettering-facing oblique | UNKNOWN | Same source video; attachment status unknown |
| 16842 | Social video screenshot | Lettering-facing | UNKNOWN | Same source video; attachment status unknown |
| 16844 | Ground-laid artwork photo | Radial panel artwork | NOT_APPLICABLE | Artwork-only reference |
| 16850 | Document photo | Competition rules | NOT_APPLICABLE | Document evidence, not a balloon view |

## State classification policy
- `BASE-UNLOADED`: use only with direct confirmation or a sufficiently clear, unobstructed reference showing the balloon's documented state without the separate Yan-Khwe.
- `DISPLAYED-ATTACHED`: use only when the balloon and separate suspended Yan-Khwe relationship are visible or explicitly confirmed by a reliable source.
- `UNKNOWN`: use when occlusion, crop, lack of provenance or uncertain interpretation prevents classification.
- `NOT_APPLICABLE`: document or isolated artwork evidence that does not depict the balloon state.

Do not infer BASE-UNLOADED from an unseen/occluded attachment area. Do not infer DISPLAYED-ATTACHED from a close-up of the Yan-Khwe alone.

## Next evidence required
1. Ask the original source owner/operator to identify the visual state of each source.
2. Obtain state-attributed views showing the full envelope and lower attachment region without obstruction, from safe and permitted viewpoints.
3. Keep each capture set to one confirmed visual state; do not combine states in a single reconstruction set.
4. Preserve original files and record SHA-256, camera metadata, viewpoint, date/time and source provenance.
5. Use overlapping views and parallax only after capture authorization and safety review.

## Gates
- State attribution: **BLOCKED**
- Calibrated photogrammetry: **BLOCKED**
- COLMAP: **NOT AUTHORIZED**
- UV mapping: **NOT READY**
- Geometry v2: **HOLD**

No source image or Geometry v1 asset was modified during this audit.
