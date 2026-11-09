# KMH_BAL_001 — Source-Owner State Confirmation v1.0

## Purpose
Obtain reliable provenance for the existing reference images before using them to compare or reconstruct the balloon's two visual states.

This form asks only for visual-state attribution and source identity. It does not request technical details about pyrotechnics, attachment construction, operation, timing, or launch.

## State definitions
- `BASE-UNLOADED`: the reference depicts the balloon envelope without the separate suspended ယမ်းခွေ (Yan-Khwe).
- `DISPLAYED-ATTACHED`: the reference depicts the balloon with the separate Yan-Khwe suspended beneath it.
- `UNKNOWN`: the state cannot be established from direct knowledge or sufficient evidence.
- `NOT_APPLICABLE`: the image is not a view of the balloon state (e.g. a document or ground-laid artwork photo).

**Do not guess.** A cropped or obstructed lower area does not prove BASE-UNLOADED. A close-up of the Yan-Khwe alone does not prove it is attached to the balloon in the same scene.

## Questions for the photographer / source owner
1. Do the images show the same balloon, team, or competition entry? Identify only what is known.
2. For each image, which state is actually depicted?
3. What supports the answer: direct presence at the event, original camera files, team record, unedited full video, or another identifiable source?
4. What year/date and category can be confirmed?
5. Are any images crops or screenshots from one video? Identify that source if known.
6. Is physical front/rear/left/right orientation known, or should it remain unknown?

## Confirmation quality levels
- `DIRECT_WITNESS`: confirmer personally witnessed the exact subject/state.
- `ORIGINAL_CREATOR`: photographer/video creator confirms the original source and state.
- `TEAM_RECORD`: identifiable team or official record confirms subject and state.
- `DOCUMENTED_SOURCE`: independently traceable source supports the attribution.
- `VISUAL_INFERENCE_ONLY`: appearance-based guess; **not sufficient** to promote an image.
- `UNKNOWN`: no adequate basis.

## Required fields for a confirmed state
A row may be promoted from UNKNOWN only when all are supplied:
- `confirmed_state` is BASE-UNLOADED or DISPLAYED-ATTACHED;
- `confirmed_by` and `relationship_to_source`;
- `confirmation_basis` is an acceptable level (not VISUAL_INFERENCE_ONLY);
- `evidence_reference` identifies the original file, source video, dated team record, or confirmation note;
- `confirmation_date`.

Keep the original file and SHA-256 unchanged. Record any new confirmation note separately.

## Existing image groups (hints, not state confirmations)
- 16812–16814: original artwork-facing balloon photographs; state unknown.
- 16822 and 16824: 2019 video screenshots showing Yan-Khwe detail; full balloon-to-attachment relationship is not visible in these frames.
- 16826–16842: screenshots from one social-video sequence; not independent calibrated captures; state unknown.
- 16844: ground-laid artwork photo; NOT_APPLICABLE to balloon state.
- 16850: photographed rules document; NOT_APPLICABLE to balloon state.

## Gate
Until state is confirmed with adequate provenance:
- state-specific photogrammetry remains blocked;
- current image usage remains qualitative only;
- Geometry v1 remains preserved;
- Geometry v2 remains HOLD.

This pack is a source-attribution tool only. It does not certify geometry or authorize operational activity.
