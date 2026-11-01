# MLCW Run #35 — Image Editing and Segmentation Research Update

**Date:** 2026-11-01  
**Scope:** controlled reconstruction, protected identity regions, transparent asset output, and garment segmentation.

## 1. OpenAI GPT Image editing capabilities

Official API reference:
https://developers.openai.com/api/reference/resources/images/methods/edit

Current reference documents:
- Multiple input images (up to 16) for GPT Image models.
- Image edit prompt plus optional mask.
- PNG/WebP transparent background output on supported GPT Image 2.5 variants.
- A mask PNG uses fully transparent pixels to indicate the areas the model may edit; it must match the first input image dimensions and be under 4 MB.
- Markup is a separate transparent overlay guidance option on supported GPT Image 2.5 variants and cannot be combined with mask.
- `input_fidelity` high/low is documented for GPT Image 1.5; do not assume that parameter applies to GPT Image 2.x.

Official image-generation guide:
https://developers.openai.com/api/docs/guides/image-generation

Important limitation stated by OpenAI: mask-based editing is prompt-guided and the model may not follow the mask's exact shape precisely. Therefore, an image-edit model cannot be the final pixel-precision QA authority for MLCW.

## 2. Meta SAM 3.1 segmentation

Official prompt guide:
https://dev.meta.ai/docs/sam/segmenting

Official overview:
https://dev.meta.ai/docs/sam/overview

SAM 3.1 accepts either a short noun-phrase concept prompt or object-specific point/box prompts. Use one prompt mode per request. Returned boxes and masks can be used for measuring, cropping and compositing. It is a mask-generation candidate, not an automatic garment-fitting or identity-preservation system.

## 3. Recommended MLCW tool division

| Task | Recommended method | Acceptance authority |
|---|---|---|
| Reconstruct hidden body areas | GPT Image edit with original Thiri reference and approved neutral-base reference; mask only permitted garment/body reconstruction regions | Human visual review |
| Protect face/hair/flower/earrings | Keep protected-region mask outside edit area; compare source/output after alignment | Pixel-diff QA + human review |
| Produce transparent candidate | Request transparent PNG/WebP background; inspect actual alpha channel | Alpha-channel pixel inspection |
| Segment P01 garments | SAM 3.1 concept and point/box prompts per blouse, longyi and drape | Human-reviewed reference masks |
| Final compositing | Deterministic layer compositing with documented anchor coordinates | Pixel QA + visual sign-off |

## 4. MLCW-specific prompt strategy

Do not ask one segmentation request for "the outfit" as a single object. Segment individual layers:
- P01 blouse / upper garment
- P01 ruby longyi
- P01 gold/cream drape
- decorative trims/accessories as separate objects where necessary

For small details or stylized boundaries, use point/box prompts and inspect each result. A broad text phrase may return unrelated matching objects or omit unusual costume elements.

## 5. Required gates before any P01 execution

1. User approves the generated neutral-base candidate visually.
2. Establish an explicit protected-region mask for face, hair/bun, flower, earrings, skin and hands.
3. Create an editable/reviewable mask for reconstructed garment/body regions.
4. Keep generated/reconstructed pixels labelled separately from source-preserved pixels.
5. Obtain clean P01 blouse, longyi and drape masks; reject clipped boundaries and neighboring fragments.
6. Use deterministic compositing and calculate target coverage, uncovered pixels, spillover and protected-region pixel changes.
7. Human review approves final result.

## 6. Current evidence boundary

- Option B reconstruction was explicitly approved by the user.
- A 1024×1536 RGB candidate on white background has been generated and saved to the user's Library.
- Candidate has not been visually approved as Master Base.
- Candidate is not transparent; no alpha matte has been generated.
- No actual P01 segmentation/composite or protected-region pixel QA has been performed.
- Synthetic QA/metric tests remain software tests only, not evidence of Thiri model accuracy.

**Run #35 status:** research updated; candidate awaits user visual approval. Next gate is approval and protected-region definition, not automatic P01 application.
