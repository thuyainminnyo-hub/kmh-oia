# KMH Myanmar Balloon 3D Intelligence — Taunggyi Night Balloon Reference Decomposition v1

**Status:** REFERENCE-INGESTED / CLAIMS-UNVERIFIED  
**Project asset:** KMH-BAL-001  
**Purpose:** High-level visual and cultural reference decomposition for a non-operational 3D heritage model.

## 1. Four-part reference taxonomy

1. **Shan-paper envelope (outer body):** visual silhouette, surface zones, paper appearance, painted narrative artwork and ornamentation.
2. **Bamboo frame / rings:** represent only as visible or documented structural-reference geometry. Exact member layout, joinery, load capacity and engineering dimensions are not established by the supplied text.
3. **Wick / heat-source assembly:** record as a named historical component and visual reference only. Do not create fabrication, fuel, treatment, ignition or operating specifications.
4. **Suspended display assembly:** keep separate from the envelope and body mesh. This is a visual/heritage asset category, not an operational pyrotechnic design.

## 2. Keep asset boundaries explicit

- `KMH-BAL-001`: balloon envelope / body and its exterior artwork.
- `KMH-BAL-001-FRM-001`: bamboo frame reference; geometry and engineering details unverified.
- `KMH-BAL-001-HT-001`: wick / heat-source visual reference only; no construction or operating detail.
- `KMH-BAL-001-ATT-001`: ယမ်းခွေ (Yan-Khwe), separately suspended reference asset, based on the user's clarification of the 2019 video.
- `KMH-BAL-001-DSP-001`: generic suspended display-frame reference category, pending confirmation whether it is identical to the Yan-Khwe asset or a distinct arrangement. Do not merge records without evidence.

## 3. Dimensions — source claims, not calibrated measurements

The supplied narrative states:
- typical night-balloon height: approximately 22–25 ft;
- reported envelope diameter / maximum body width: approximately 18–25 ft (5.49–7.62 m);
- payload mass: reported as over 20 viss / approximately 40 lb.

These are secondary-source claims supplied as background context, not independently verified dimensions of this specific balloon.

## 4. User-provided size identification record

The user supplied these dimensions for KMH-BAL-001:

| Parameter | Value | Metric equivalent | Status |
|---|---:|---:|---|
| Body circumference (လုံးပတ်အရှည်) | 75 ft | 22.86 m | USER_PROVIDED_DIMENSION |
| Overall height (အမြင့်) | 25 ft | 7.62 m | USER_CONFIRMED_MEASUREMENT; provenance pending |
| Top circular diameter (ခေါင်အဝိုင်းအချင်း) | 25 ft | 7.62 m | USER_PROVIDED_DIMENSION |
| Bottom circular diameter (အောက်ခြေအဝိုင်းအချင်း) | 7 ft or 7.5 ft | 2.13 m or 2.29 m | USER_PROVIDED_RANGE; exact value pending |

**Terminology:** အချင်း (Diameter) means the straight-line width from one side of the balloon body to the other. လုံးပတ် (Circumference) means the length measured around the body. They are different measurements and must not be interchanged.

**Consistency note:** If 75 ft is the circumference of a circular cross-section, the equivalent diameter is about 23.87 ft. A 25 ft diameter circle has a circumference of about 78.54 ft. Preserve both user-provided values as separate measurements until the exact measurement path/plane is clarified; do not silently reconcile them.

The earlier 18–25 ft diameter figure remains a general secondary-source range, not a measured value for this specific balloon.

## 5. Measurement glossary — user-confirmed terminology

- **အချင်း (Diameter):** မီးပုံးပျံကိုယ်ထည်ရဲ့ တစ်ဖက်မှတစ်ဖက် အကျယ်။ English: the straight-line width across the balloon body through a specified cross-section. Record as `maximum_body_diameter` or the relevant ring diameter.
- **လုံးပတ် (Circumference):** မီးပုံးပျံကိုယ်ထည်ကို ပတ်တိုင်းထားတဲ့ အလျား. English: the distance around the balloon body. Record as `body_circumference`.

## 6. Visual modelling scope

Allowed project work:
- envelope silhouette and surface segmentation;
- separate, non-operational visual placeholders for documented frame/component categories;
- artwork and ornament UV planning;
- asset provenance, source confidence and uncertainty labels;
- competition-rule compliance mapping at a non-operational level.

Out of scope:
- pyrotechnic recipes, quantities, assembly, wiring, fuse timing, ignition, firing sequence, lift calculations for a pyrotechnic payload, or operational deployment instructions;
- engineering certification, structural safety claims, or real-world construction guidance.

## 7. Evidence and confidence rules

- Preserve the user's supplied narrative and its cited URLs as a source lead, not as independently verified facts.
- Attribute each numerical claim to its source and keep it separate from measured geometry.
- Do not infer a circular cross-section from a stated diameter unless supported by orthogonal views or measurements.
- Do not merge the Yan-Khwe, suspended display frame, and balloon envelope into one mesh or asset record without direct evidence.
- Keep Geometry Blockout v1 unchanged until physical dimensions are independently documented.

## 8. Next evidence needed

1. Clarify whether the 75 ft circumference is measured around the widest body section or another path.
2. Confirm whether the bottom circular diameter is 7 ft or 7.5 ft.
3. Obtain orthogonal photographs or measured drawings for width/depth and ring placement.
4. Record measurement method, date, operator, instrument and tolerance; independently review before Geometry v2 calibration.

**Current decision:** user-provided dimensions have been recorded; keep physical scale calibration on HOLD until the measurement path, bottom diameter and provenance are resolved. No pyrotechnic construction or operating details are to be modelled or documented.
