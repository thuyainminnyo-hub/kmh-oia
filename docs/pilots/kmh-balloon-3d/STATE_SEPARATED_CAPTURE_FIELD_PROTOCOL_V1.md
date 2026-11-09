# KMH_BAL_001 — State-Separated Capture Field Protocol v1.0

## 1. Objective
Acquire a traceable, non-operational visual dataset for 3D heritage reconstruction of one identified balloon envelope. Each physical visual state must be collected as a separate capture set:
- `BASE-UNLOADED`
- `DISPLAYED-ATTACHED`
- `UNKNOWN` — use when a knowledgeable source cannot confirm the state.

Do not combine images from different states in one photogrammetry set. UNKNOWN images may be preserved for visual reference, but they are not eligible for a state-specific reconstruction run.

This protocol documents appearance only. It does not cover balloon operation, pyrotechnics, attachment construction, ignition, launch, or flight performance.

## 2. Safety and permission boundary
- Photograph only an already stationary, safely accessible display or documented object, with the owner's/event authority's permission.
- Do not approach, touch, climb, move, load, unload, suspend, or alter the balloon or any attached item for photography.
- Do not enter restricted, crowd-control, flight, fire, or work zones.
- Do not use ladders, roofs, elevated platforms, drones, or other access methods unless independently authorized and managed by the responsible site authority. If a view is not safely available, mark it NOT_CAPTURED.
- Do not delay or interfere with an event, team, or safety personnel.
- A state must be confirmed by the source owner/operator or a clearly documented, unobstructed reference; never infer BASE-UNLOADED merely because the lower area is cropped or hidden.
- Stop capture if site conditions change or the responsible authority asks the team to stop.

## 3. Separate capture-set design
Create one folder and one manifest per visual state and physical subject:

```text
KMH-BAL-001/
  BASE-UNLOADED/
    originals/
    working_copies/
    manifest.json
  DISPLAYED-ATTACHED/
    originals/
    working_copies/
    manifest.json
  UNKNOWN/
    originals/
    working_copies/
    manifest.json
```

Use UNKNOWN only for unconfirmed references. Do not move an image from UNKNOWN into a confirmed state without recording who confirmed it, when, and on what evidence.

Each set must refer to one balloon/team identity, competition year or capture date, stable visual state, and camera/lens configuration where practical. If the state changes, close the current set and open a new one.

## 4. View coverage plan
Record which views are captured and which are unavailable. Use different camera positions, not only camera rotation from one standing point.

| View group | Capture intent | Coverage rule |
|---|---|---|
| Front / Buddha-facing | Main front artwork and envelope contour | Keep full visible envelope in frame |
| Rear / lettering-facing | Lettering and opposite contour | Preserve complete visible text region |
| Side narrative-facing | Narrative artwork and profile | Physical left/right orientation must be confirmed |
| Left oblique | Connect adjacent surfaces | Obtain overlap with front and rear views |
| Right oblique | Connect adjacent surfaces | Obtain overlap with front and rear views |
| Upper view | Crown/upper surface, only where safely accessible | Otherwise NOT_CAPTURED with reason |
| Lower view | Lower envelope/ring region, only where safely accessible | Do not approach restricted or hazardous areas |
| Detail views | Artwork, seams, edges, markings | Retain a wider context image per detail |

COLMAP recommends strong image overlap, different viewpoints, good visible texture, similar illumination, and having each object region visible in at least three images. Treat this as a planning guideline, not a guarantee. If the physical scene does not permit a safe view, record the gap rather than forcing coverage. (COLMAP tutorial: https://colmap.github.io/tutorial.html)

## 5. Camera and image handling
- Prefer the same camera body and lens/module throughout one set.
- Keep focal length / zoom fixed within a set where practical; record any lens/module change.
- Preserve original files and EXIF metadata. Never overwrite originals.
- Do not use digital zoom, portrait-mode depth effects, filters, perspective correction, HDR compositing, AI enhancement, denoising, or in-camera panorama stitching for the originals.
- Avoid motion blur, clipped highlights, strong backlighting, moving foreground people, and changing illumination.
- Aim for consistent exposure and white balance across one set.
- If camera calibration is available, record calibration file, camera model, image dimensions, and calibration date. EXIF alone is not camera calibration.
- Put crops, rotations, retouches, or color-adjusted derivatives only under working_copies/, with a processing log linked to the original hash.

## 6. Scale and measurement evidence
Scale must come from independently measured control information, not visual guessing.
- Use a known scale reference or surveyed control distance only where permitted and without attaching anything to the balloon.
- Record reference ID, measured length, units, endpoints, instrument, operator, date, uncertainty/tolerance, and spatial relationship to the subject.
- If no reliable scale reference is available, mark scale_control = NOT_AVAILABLE and keep reconstruction unscaled.
- Keep these user-confirmed values semantically distinct: 25 ft overall height, 75 ft maximum-body circumference, 7.5 ft bottom-ring diameter, and 25 ft top-ring diameter. Mark them owner-reported unless an independent measurement record is attached.
- Never substitute circumference for diameter or infer width/depth from height alone.

## 7. Required manifest fields
Per capture set: set ID, state ID, source of state confirmation, subject/team identity, competition year/date; operator, capture date/time, device, camera module/lens, focal length, image size, lighting/environment; permissions reference; scale control and measurement provenance; coverage matrix; image filename, SHA-256, EXIF status, viewpoint, sharpness/occlusion review, and original/derivative relationship.

## 8. Acceptance gates before COLMAP
Do not start state-specific SfM/MVS until all required gates pass:
1. State confirmed as BASE-UNLOADED or DISPLAYED-ATTACHED.
2. All images belong to the same subject and stable state.
3. Original images and hashes preserved.
4. Viewpoint diversity, overlap and parallax adequate for visible surface.
5. Sharpness, exposure and lighting acceptable.
6. Camera/lens metadata recorded; calibration provenance explicit.
7. Scale source and uncertainty recorded, or output explicitly left unscaled.
8. Missing/unsafe views declared and accepted by human reviewer.
9. Human reviewer authorizes the specific set.

UNKNOWN state, mixed-state set, missing source provenance, unverified scale, or unsafe/missing critical views keeps COLMAP blocked.

## 9. State-specific reconstruction and comparison
Run separate workspaces for BASE and DISPLAYED states. Align results only after each state has its own scale and coordinate-control evidence. Compare envelope silhouette/profile, crown, maximum-body region, lower contour, measured dimensions, residuals, coverage holes, camera registration, and source provenance.

Do not infer attachment mechanics or calculate any change from the reported Yan-Khwe weight. A state-specific mesh is created only if independent evidence demonstrates a repeatable geometric difference and a human reviewer approves it.

## 10. Current project gate
- Existing 16 references: state attribution unresolved; not a calibrated capture set.
- New state-separated capture: REQUIRED.
- COLMAP: BLOCKED until set-specific QA and human approval.
- UV mapping: NOT READY.
- Geometry v1: PRESERVED.
- Geometry v2: HOLD.
- Production: NOT AUTHORIZED.
