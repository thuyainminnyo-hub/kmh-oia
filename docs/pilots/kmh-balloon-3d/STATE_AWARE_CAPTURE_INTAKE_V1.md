# KMH_BAL_001 — State-aware Capture Intake v1.0

## Purpose
Collect new visual evidence for the two documented appearance states without mixing images from different states into one photogrammetry set.

## Required visual-state labels
- `BASE-UNLOADED`: envelope reference without the separate Yan-Khwe attachment.
- `DISPLAYED-ATTACHED`: displayed reference with the separate Yan-Khwe visual attachment.
- `UNKNOWN`: use whenever the state cannot be established from source provenance or direct confirmation.

Do not guess a state from appearance alone. Each capture set should contain one stable visual state. If state changes during the session, start a separate set.

## View groups
Front / Buddha-facing; rear / lettering-facing; side narrative-facing; left and right oblique; upper and lower views only from safe, permitted viewpoints; and detail views for artwork, seams and surface features.

The physical left/right orientation of the narrative image must be confirmed rather than inferred.

## Preserve originals
- Keep original camera files unchanged and preserve EXIF metadata.
- Put crops, rotations, color correction and annotations in a separate working-copy directory.
- Record SHA-256, image dimensions, filename, sequence number and view label.

## Measurement provenance
For every measured dimension, record feature definition and endpoints, value/unit, method/instrument, date/operator, state label, uncertainty/tolerance and independent-verification status.

Do not infer width, depth or a state-specific profile from height alone or from uncalibrated perspective photographs.

## Capture-quality review
Review subject identity, state consistency, viewpoint diversity, overlap, parallax, lighting, sharpness, occlusion, scale reference and metadata completeness.

COLMAP processing remains blocked until the capture set passes human review. Tripo paid generation requires separate explicit approval.

## Current supplied references
Original files 16812, 16813 and 16814 remain qualitative artwork references. Their base/attached state attribution is UNKNOWN and they are not a calibrated photogrammetry set.

## Status
This is an intake template, not evidence that a new capture has occurred. Geometry v1 remains preserved; Geometry v2 remains HOLD.
