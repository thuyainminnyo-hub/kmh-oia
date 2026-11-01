# MLCW V1.0.8 — Run #39 Fine-Edge Inspection & Identity Comparison

**Date:** 2026-11-01  
**Candidate:** `MLCW_Run36_CandidateB_GlowSuppressed.png`  
**Decision:** PARTIAL EDGE PASS / IDENTITY NOT VERIFIED / MASTER BASE HOLD

## 1. Fine-edge crop inspection

Six regions were cropped from the 1024×1536 RGBA candidate and enlarged to 200% on a saturated magenta inspection background.

| Region | Observation | Result |
|---|---|---|
| Hair bun / white flower | Silhouette visible; minor fringe/edge-cleanup required | PARTIAL |
| Face / earrings | Visible, but generated features differ from source reference | REVIEW |
| Left hand | Silhouette readable; no major finger-gap loss seen | PRELIMINARY PASS |
| Right hand | Silhouette readable; no major finger-gap loss seen | PRELIMINARY PASS |
| Skirt hem | Edge readable; no obvious clipping | PRELIMINARY PASS |
| Feet / toes | Contours readable; no obvious clipping | PRELIMINARY PASS |

This is visual inspection, not a pixel-perfect human annotation.

## 2. Alpha measurements from actual PNG

- Dimensions: 1024×1536; mode RGBA.
- Alpha min/max: 0 / 255.
- Fully transparent pixels: 1,191,336.
- Partially transparent pixels: 15,235.
- Fully opaque pixels: 366,293.
- Nonzero-alpha connected components: 1.
- Nonzero-alpha bounding box: `[134,22,884,1502]`.
- SHA-256: `e78e451a467c23bbf38d5b1701d8f8837d973dd58bb214cf9202f1e0749d50da`.

## 3. Original-vs-candidate identity comparison

A same-canvas crop comparison was produced for face core, hair/flower, earrings/neck and whole head.

Exploratory raw RGB SSIM:
- Face core: 0.516694.
- Hair + flower: 0.447878.
- Earrings + neck: 0.516999.
- Whole head: 0.480410.

**Interpretation warning:** these raw RGB SSIM values are not accepted as identity-similarity scores. No landmark registration or region-specific protected masks were applied, and candidate is newly generated artwork with different color, lighting and rendered details. The score is not a valid identity pass/fail metric.

Visual review indicates broad stylistic similarity, but the generated facial features, hair volume and accessory details are not exact copies of original source pixels. Thus original-pixel identity preservation is not established.

## 4. Evidence artifacts in Library

- `/My Little Creative World/Run 39/Thiri_Edge_Inspection_200pct.jpg`
- `/My Little Creative World/Run 39/Thiri_Original_vs_Candidate_Head.jpg`
- `/My Little Creative World/Run 39/Identity_Comparison_Metrics.json`

## 5. Research-informed next approach

OpenAI's current image prompting guide recommends checking alpha directly, comparing quality on representative inputs, and explicitly requesting transparent backgrounds with crisp silhouette/no halos. It also says to inspect details and ensure the edit changed only the requested content.

SAM 3.1 accepts either short concept phrases or object-specific box/point prompts (not both modes in one request). Use this to create localized masks, but treat them as candidates requiring human correction.

**Recommended identity-preserving revision:** preserve the original Thiri head/face/hair/flower/earring pixels from the canonical reference using a human-reviewed protected mask, and reconstruct only the clothed body regions beneath the head. This may preserve the original identity more faithfully than generating the entire character again. A careful neck/hairline seam blend and alignment check will be required.

## 6. Gate status

- Alpha technical integrity: PASS.
- Multi-background full-frame readability: preliminary PASS.
- Hair/flower fine-edge cleanup: PARTIAL.
- Hand/skirt/feet edge readability: preliminary PASS.
- Face/hair identity: NOT VERIFIED.
- Master Base approval: HOLD.
- P01 segmentation/composite: NOT RUN.

## Official references
- OpenAI image prompting: https://developers.openai.com/api/docs/guides/image-prompting
- OpenAI Image Edit API: https://developers.openai.com/api/reference/resources/images/methods/edit
- Meta SAM 3.1 segmentation: https://dev.meta.ai/docs/sam/segmenting

**Run #39 result:** crop-level inspection completed; the current generated candidate is not approved as Master Base. Preserve original protected head pixels in the next reconstruction iteration.
