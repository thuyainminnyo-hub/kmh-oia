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

**User clarification:** Record the 18–25 ft figure as the reported maximum body diameter / width range for the balloon envelope. In dimensional terminology, diameter is the straight-line width across the body; circumference is the distance around it. This is a `REFERENCE_ESTIMATED_RANGE`, not a direct measurement of the specific balloon being reconstructed. Do not choose a single value within the range or scale Geometry v1 from it until the exact balloon's width is measured or independently corroborated. The user's separately confirmed 25 ft (7.62 m) height remains `USER_CONFIRMED_MEASUREMENT`, with method, date, operator, tolerance and independent corroboration still pending.

## 4. Measurement glossary — user-confirmed terminology

- **အချင်း (Diameter):** မီးပုံးပျံကိုယ်ထည်ရဲ့ တစ်ဖက်မှတစ်ဖက် အကျယ်။ English: the straight-line width across the balloon body through its widest cross-section. Record in the project as `maximum_body_diameter` / `maximum_body_width`.
- **လုံးပတ် (Circumference):** မီးပုံးပျံကိုယ်ထည်ကို ပတ်တိုင်းထားတဲ့ အလျား။ English: the distance around the balloon body. Do not use this term for diameter.

For this project, the user's intended meaning is explicit: **18–25 ft refers to the balloon body's diameter / across-body width, not its circumference.** Retain this terminology in all future geometry, measurement, and evidence records.

## 5. Visual modelling scope

Allowed project work:
- envelope silhouette and surface segmentation;
- separate, non-operational visual placeholders for documented frame/component categories;
- artwork and ornament UV planning;
- asset provenance, source confidence and uncertainty labels;
- competition-rule compliance mapping at a non-operational level.

Out of scope:
- pyrotechnic recipes, quantities, assembly, wiring, fuse timing, ignition, firing sequence, lift calculations for a pyrotechnic payload, or operational deployment instructions;
- engineering certification, structural safety claims, or real-world construction guidance.

## 6. Evidence and confidence rules

- Preserve the user's supplied narrative and its cited URLs as a source lead, not as independently verified facts.
- Attribute each numerical claim to its source and keep it separate from measured geometry.
- Do not infer a circular cross-section from a stated diameter unless supported by orthogonal views or measurements.
- Do not merge the Yan-Khwe, suspended display frame, and balloon envelope into one mesh or asset record without direct evidence.
- Keep Geometry Blockout v1 unchanged until physical dimensions are independently documented.

## 7. Next evidence needed

1. Full, legible competition-rule page(s) for rule transcription and compliance mapping.
2. Direct orthogonal photographs or measured drawings for envelope width/depth and visible ring placement.
3. Source-specific confirmation of whether the 18–25 ft diameter claim applies to this exact balloon or only to a general class.
4. Independent review of all dimensions before Geometry v2 scale calibration.

**Current decision:** update the reference taxonomy and visual asset map; keep physical scale calibration on HOLD. No pyrotechnic construction or operating details are to be modelled or documented.
