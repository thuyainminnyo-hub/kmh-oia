# MLCW V1.0.8 — Run #39 Fine-Edge Inspection & Identity Comparison

**Date:** 2026-11-01  
**Asset reviewed:** `MLCW_Run36_CandidateB_GlowSuppressed.png`  
**Dimensions:** 1024×1536 RGBA  
**SHA-256:** `e78e451a467c23bbf38d5b1701d8f8837d973dd58bb214cf9202f1e0749d50da`

## 1. Fine-edge crops (200%)

| Region | Observation | Result |
|---|---|---|
| Hair bun / white flower | Edges readable; minor edge-fringing and fine-strand cleanup remain | PARTIAL |
| Face / earrings | Features visible; generated face/hair details differ from source | REVIEW |
| Left hand | Silhouette readable; no major finger-gap loss observed | PRELIMINARY PASS |
| Right hand | Silhouette readable; no major finger-gap loss observed | PRELIMINARY PASS |
| Skirt hem | Edge readable; no major clipping observed | PRELIMINARY PASS |
| Feet / toes | Contours readable; no major clipping observed | PRELIMINARY PASS |

## 2. Actual alpha measurements

- Alpha min/max: 0 / 255.
- Fully transparent pixels: 1,191,336.
- Partially transparent pixels: 15,235.
- Fully opaque pixels: 366,293.
- Nonzero-alpha connected components: 1.
- Main nonzero-alpha bbox: `[134,22,884,1502]`.

## 3. Identity comparison — limitation

The original Thiri reference and generated candidate were compared in same-canvas crop coordinates. Exploratory raw RGB SSIM values were:
- Face core: 0.516694
- Hair + flower: 0.447878
- Earrings + neck: 0.516999
- Whole head region: 0.480410

**These values are not accepted as identity-similarity scores.** No landmark registration or region-specific segmentation masks were applied, and the generated candidate includes different background/lighting/appearance. The correct decision is manual review pending, not numeric pass/fail.

The side-by-side comparison visually suggests the broad character styling is similar, but generated details in face, hair volume, earring details and expression are not pixel-identical to the canonical source. Generated pixels are reconstructed, not original.

## 4. Saved evidence

- `/My Little Creative World/Run 39/Thiri_Edge_Inspection_200pct.jpg`
- `/My Little Creative World/Run 39/Thiri_Original_vs_Candidate_Head.jpg`
- `/My Little Creative World/Run 39/Identity_Comparison_Metrics.json`

## 5. Gate decision

- Edge readability (hands, skirt hem, feet): preliminary pass.
- Hair/flower edge cleanup: partial; manual correction required.
- Face/hair identity consistency: not independently verified.
- Master Base approval: HOLD pending user review.
- P01 segmentation/compositing: not run.

## 6. Research notes

SAM 3.1 supports either a short concept noun phrase or object-specific boxes/points. For small garment panels, localized prompts are preferable to broad concept requests. Model masks are returned as measurable geometry; they do not prove garment fit or identity preservation.

OpenAI image edits can request transparent output and use PNG masks, but the edit remains generative; MLCW must continue deterministic post-edit QA.

Official sources:
- Meta SAM prompt guidance: https://dev.meta.ai/docs/sam/segmenting
- Meta SAM overview: https://dev.meta.ai/docs/sam/overview
- OpenAI Image Edit API: https://developers.openai.com/api/reference/resources/images/methods/edit
- OpenAI transparent cutout prompt guide: https://developers.openai.com/api/docs/guides/image-prompting

**Run #39 result:** crop-level inspection completed; edge quality partial; identity QA unresolved; Master Base remains HOLD; P01 composite not run.
