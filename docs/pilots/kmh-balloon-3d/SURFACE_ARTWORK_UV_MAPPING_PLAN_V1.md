# KMH-BAL-001 Surface Artwork & UV Mapping Plan v1

Status: production planning specification. No final UV unwrap, texture bake, or verified artwork extraction has been executed.

## 1. Geometry separation
- `KMH-BAL-001-BODY`: main inflated shell.
- `KMH-BAL-001-SKIRT`: lower radial/ornamental fabric zone, modeled as a visually connected but separately addressable mesh region until construction evidence confirms the physical seam.
- `KMH-BAL-001-ART-*`: artwork/texture regions assigned to the body; these are material/UV zones, not separate physical panels unless seams are visible and verified.
- `KMH-BAL-001-ATT-001`: ယမ်းခွေ (Yan-Khwe), separate suspended reference asset. Excluded from balloon shell geometry and UV atlas.

## 2. Surface zones
| Zone ID | Visual region | Reference evidence | Mapping approach | Status |
|---|---|---|---|---|
| Z01 | Upper fire/orange gradient | New front/rotating-view screenshots | Cylindrical/parametric body UV; preserve gradient continuity | Reference identified |
| Z02 | Large lettering | Front-facing screenshot | Dedicated high-resolution UV island or decal projection; preserve glyph proportions | Reference identified; exact text needs transcription |
| Z03 | Buddha and halo | Narrative artwork screenshots | Dedicated high-resolution UV island; minimize distortion around focal figure and circular halo | Reference identified |
| Z04 | Surrounding narrative figures | Narrative artwork screenshots | Adjacent dedicated UV region; align continuity with Z03 | Reference identified |
| Z05 | Lower dark transition band | Multiple body views | Continuous body UV region; capture fold/seam variation from source | Reference identified |
| Z06 | Lower radial ornament | Inflated views and ground-laid radial panel view | Radial UV layout; preserve center-to-perimeter symmetry only where visible | Reference identified |
| Z07 | Rear/side artwork and lettering | Rotating-view screenshots | Separate UV region after orientation is established | Partial; orientation pending |

## 3. Coordinate and orientation convention
- Define front as the Buddha-facing focal side for this project unless the user supplies a different canonical front.
- Define rear as the opposite side only after a complete visual orbit or source video confirms it.
- Do not label left/right from a single perspective screenshot; store camera viewpoint and rotation sequence when available.
- Use a consistent object coordinate system: Z up; front direction marked on the asset manifest; apply transforms before final UV production.

## 4. Texture production rules
- Preserve original uploaded screenshots as immutable evidence; create derived crops only in a separate working directory.
- Do not AI-recreate lettering or religious/narrative artwork as if it were the original. Mark any reconstruction as derived artwork and retain a link to its source reference.
- Keep lettering as vector/decal where practical until exact text and spelling are verified.
- Use a checker texture to inspect UV stretch before painting or baking.
- Maintain sufficient texel density for focal Buddha/halo and lettering zones; use a separate UDIM/tile or higher-resolution atlas if a single atlas cannot preserve detail.
- Avoid blending screenshots across different inflation states or video transitions.

## 5. Validation gates
1. Reference provenance: every texture crop traces to a source image/frame and SHA-256.
2. Orientation: front/rear/left/right labels confirmed; uncertain labels remain unknown.
3. UV distortion: checker pattern shows acceptable stretch over body and radial skirt.
4. Artwork fidelity: lettering transcription, focal Buddha/halo placement, and narrative continuity reviewed against source.
5. Seam continuity: gradient and ornament boundaries checked at the 0/360-degree seam.
6. Scale: texture layout is independent of physical scale; 7.62 m height remains user-confirmed and independently unverified.
7. Approval: independent visual QA and explicit human approval before production promotion.

## 6. Current blockers
- No original source video file or uncompressed camera photos.
- Exact lettering transcription and complete surface orbit not yet confirmed.
- No measured body circumference, width or depth.
- No final production mesh or Blender `.blend` master.
- No UV unwrap, texture bake, or artwork extraction has been executed.

## 7. Release status
PLANNED — not executed. This document defines the next controlled production task; it does not certify a finished texture or 3D asset.