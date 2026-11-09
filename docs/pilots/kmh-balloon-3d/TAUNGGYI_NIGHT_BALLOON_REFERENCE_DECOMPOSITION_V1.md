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

| Parameter | Value | Metric equivalent | Status |
|---|---:|---:|---|
| Maximum-body circumference (အကျယ်ဆုံးနေရာ၏ လုံးပတ်အရှည်) | 75 ft | 22.86 m | USER-PROVIDED; path confirmed |
| Overall height (အမြင့်) | 25 ft | 7.62 m | USER-CONFIRMED; provenance pending |
| Top circular diameter (ခေါင်အဝိုင်းအချင်း) | 25 ft | 7.62 m | USER-PROVIDED |
| Bottom circular diameter (အောက်ခြေအဝိုင်းအချင်း) | **7.5 ft** | **2.29 m** | USER-CONFIRMED |

**Terminology:** အချင်း (Diameter) means the straight-line width from one side of the balloon body to the other. လုံးပတ် (Circumference) means the length measured around the body. They are different measurements and must not be interchanged.

**Measurement path:** The user confirmed that 75 ft is measured around the balloon body's widest section. If that section were perfectly circular, the equivalent diameter would be about 23.87 ft; retain the supplied circumference as the primary value and do not infer an exact width without cross-section evidence. The top diameter is a separate measurement at the top ring plane.

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

1. Confirm the exact measurement plane for the 25 ft top circular diameter.
2. Obtain orthogonal photographs or measured drawings for width/depth and ring placement.
3. Record measurement method, date, operator, instrument and tolerance; independently review before Geometry v2 calibration.

**Current decision:** user-provided dimensions have been updated, including the confirmed 7.5 ft bottom ring; keep physical scale calibration on HOLD until measurement provenance, top-ring plane and orthogonal section dimensions are documented. No pyrotechnic construction or operating details are to be modelled or documented.
