# KMH Balloon 3D — Measurement & Calibration Gate v1

**Status:** OPEN — measurement inputs incomplete  
**Asset:** KMH-BAL-001 (balloon body)  
**Related asset:** KMH-BAL-001-ATT-001 — ယမ်းခွေ (Yan-Khwe), separate suspended reference asset  
**Baseline:** Geometry Blockout v1 remains unchanged  
**Decision:** Do not scale or promote Geometry v2 until the minimum dimensional evidence below is recorded.

## 1. Confirmed and unknown dimensions

| Parameter | Current value | Evidence status | Notes |
|---|---:|---|---|
| Overall body height | 25 ft / 7.62 m | USER_CONFIRMED_MEASUREMENT | Measurement method, date, operator, tolerance and independent corroboration are not yet recorded. |
| Maximum body width / diameter | Unknown | MISSING | Required for a defensible first scale calibration. |
| Front-to-back depth | Unknown | MISSING | Do not assume a circular or rotationally symmetric planform. |
| Crown / top profile | Unknown | VISUAL_REFERENCE_ONLY | Needs calibrated views or direct measurement. |
| Lower taper and skirt dimensions | Unknown | VISUAL_REFERENCE_ONLY | Keep skirt separately addressable until seam evidence is available. |

## 2. Measurement record template

Record each measurement as a separate observation. Do not overwrite raw observations with an average.

- measurement_id: unique ID
- asset_id: KMH-BAL-001
- parameter: overall_height | max_width | front_back_depth | crown_width | skirt_diameter | other
- value: numeric value
- unit: ft | m | in | cm
- method: tape | laser_distance_meter | surveyed_reference | calibrated_photogrammetry | other
- measurement_location: where the endpoints / measurement plane were taken
- date_time: ISO 8601 with timezone
- operator: person or team
- instrument: make/model and calibration status, if applicable
- uncertainty_or_tolerance: numeric value and unit, or explicitly unknown
- raw_evidence: photo/video/file reference
- review_status: unreviewed | independently_checked | accepted | rejected
- notes: conditions, balloon state, deformation, wind, suspension, etc.

## 3. Minimum evidence required before Geometry v2

1. Record maximum width at the widest body cross-section, with a photo showing the measurement endpoints or a clearly identified measurement plane.
2. Record front-to-back depth independently. Do not substitute width unless the shape is demonstrated to be circular.
3. Re-record or corroborate the 7.62 m height with method, date, operator and tolerance.
4. Capture a scale reference in at least two orthogonal views, where practical.
5. Preserve original images and metadata; calculate SHA-256 hashes for the evidence manifest.
6. Have a second reviewer check the measurement record before applying scale to the mesh.

## 4. Calibration rules

- Preserve Geometry Blockout v1 as an immutable baseline.
- Store physical dimensions separately from normalized geometry parameters.
- Apply scale only after the measurement record is accepted.
- If width and depth differ, retain a non-circular cross-section; do not force radial symmetry.
- Keep the balloon body, lower skirt and ယမ်းခွေ as separate asset records / mesh objects unless physical evidence proves a different boundary.
- Do not infer pyrotechnic construction or operation from visual references.

## 5. Gate decision

**Current gate: HOLD — NOT READY FOR PHYSICAL SCALE CALIBRATION.**

Reason: height is user-confirmed, but width and depth are missing; measurement provenance and uncertainty are incomplete.

**Pass condition:** minimum dimensions are recorded with traceable evidence and independently reviewed. Only then create Geometry v2 and run dimensional, topology, silhouette and cross-section QA.

## 6. Current non-claims

This gate does not certify the original balloon's engineering design, structural safety, material properties, internal supports, attachment strength, or pyrotechnic safety. Geometry v1 remains a normalized topology blockout, not a measured reconstruction or production-ready model.
