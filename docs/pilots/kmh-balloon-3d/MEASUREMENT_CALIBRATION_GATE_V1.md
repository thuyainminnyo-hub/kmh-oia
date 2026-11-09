# KMH Balloon 3D — Measurement & Calibration Gate v1

**Status:** OPEN — dimensions recorded; verification and provenance still incomplete  
**Asset:** KMH-BAL-001 (balloon body)  
**Related asset:** KMH-BAL-001-ATT-001 — ယမ်းခွေ (Yan-Khwe), separate suspended reference asset  
**Baseline:** Geometry Blockout v1 remains unchanged  

## 1. User-provided size record

The user supplied the following dimensions for the balloon size identification record. These are recorded as `USER_PROVIDED_DIMENSION`, not independently surveyed measurements; measurement date, method, operator, instrument and tolerance are not yet supplied.

| Parameter | User-provided value | Metric conversion | Evidence status |
|---|---:|---:|---|
| Maximum-body circumference / အကျယ်ဆုံးနေရာ၏ လုံးပတ်အရှည် | 75 ft | 22.86 m | USER_PROVIDED_DIMENSION; measurement path confirmed by user |
| Overall height / အမြင့် | 25 ft | 7.62 m | USER_CONFIRMED_MEASUREMENT; provenance pending |
| Top circular opening/ring diameter / ခေါင်အဝိုင်းအချင်း | 25 ft | 7.62 m | USER_PROVIDED_DIMENSION |
| Bottom circular opening/ring diameter / အောက်ခြေအဝိုင်းအချင်း | **7.5 ft** | **2.29 m** | **USER_CONFIRMED_DIMENSION** |

### Terminology lock

- **အချင်း (Diameter):** မီးပုံးပျံကိုယ်ထည်ရဲ့ တစ်ဖက်မှတစ်ဖက် အကျယ်။
- **လုံးပတ် (Circumference):** မီးပုံးပျံကိုယ်ထည်ကို ပတ်တိုင်းထားတဲ့ အလျား။
- Do not use diameter and circumference interchangeably.

### Confirmed measurement path and consistency note

**User clarification:** the 75 ft circumference is measured around the balloon body's widest section.

For reference only, if that cross-section were a perfect circle, 75 ft circumference would correspond to a diameter of approximately 23.87 ft (7.28 m). A 25 ft diameter circle would have a circumference of approximately 78.54 ft (23.94 m). The measured cross-section may not be perfectly circular; therefore, retain 75 ft as the directly supplied circumference and do not replace it with the derived diameter. Keep the 25 ft top-ring diameter as a separate measurement at its own plane.

The bottom ring diameter is now specified as 7.5 ft (2.29 m), replacing the earlier 7–7.5 ft uncertainty.

## 2. Still unknown / to be clarified

- Whether the 25 ft top circular diameter is the crown/top ring diameter, and its exact measurement plane.
- Across-body width and front-to-back depth at the widest body cross-section, if distinct; the circumference alone does not determine both dimensions unless the section shape is known.
- Measurement method, date, operator, instrument and uncertainty/tolerance for each value.

## 3. Measurement record template

Record each measurement as a separate observation. Do not overwrite raw observations with an average.

- measurement_id: unique ID
- asset_id: KMH-BAL-001
- parameter: overall_height | max_section_circumference | max_body_diameter | top_ring_diameter | bottom_ring_diameter | front_back_depth | other
- value: numeric value
- unit: ft | m | in | cm
- method: tape | laser_distance_meter | surveyed_reference | calibrated_photogrammetry | other
- measurement_location: exact endpoints or measurement plane
- date_time: ISO 8601 with timezone
- operator: person or team
- instrument: make/model and calibration status, if applicable
- uncertainty_or_tolerance: numeric value and unit, or explicitly unknown
- raw_evidence: photo/video/file reference
- review_status: unreviewed | independently_checked | accepted | rejected
- notes: object state, deformation, environmental conditions and other context

## 4. Gate requirements before Geometry v2

1. Confirm whether the top circular diameter is specifically the crown/top ring and document its plane.
2. Record orthogonal width/depth evidence at the widest body section; do not infer a circular cross-section from circumference alone.
3. Capture scale references in orthogonal views where practical.
4. Preserve originals and metadata; calculate SHA-256 hashes for the evidence manifest.
5. Have a second reviewer check the dimensional record before applying physical scale.

## 5. Calibration rules

- Preserve Geometry Blockout v1 as an immutable baseline.
- Store physical dimensions separately from normalized geometry parameters.
- Apply physical scale only after the measurement record is accepted.
- Keep body, lower skirt and ယမ်းခွေ as separate asset records / mesh objects unless evidence proves a different boundary.
- Do not infer pyrotechnic construction or operation from visual references.

## 6. Current gate decision

**HOLD — DIMENSIONS RECORDED, GEOMETRY V2 SCALE NOT YET APPROVED.**

Reason: the 75 ft circumference measurement path is user-confirmed as the widest body section and the bottom diameter is now specified as 7.5 ft, but measurement provenance and uncertainty, the exact top-ring plane, and orthogonal section dimensions remain unresolved. Geometry v1 remains a normalized topology blockout, not a measured reconstruction or production-ready model.

This gate does not certify engineering design, structural safety, material properties, internal supports, attachment strength, or pyrotechnic safety.
