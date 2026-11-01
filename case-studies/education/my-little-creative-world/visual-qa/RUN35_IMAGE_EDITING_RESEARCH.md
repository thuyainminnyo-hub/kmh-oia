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


## 7. Precision constraints confirmed from current official API references

### OpenAI GPT Image 2.5 edit
- Up to 16 input images can be supplied to GPT Image edit.
- For supported GPT Image 2.5 variants, `background="transparent"` is supported; use PNG or WebP to retain alpha.
- A mask must be PNG, under 4 MB, and match the first input image dimensions. Fully transparent mask pixels indicate areas that may be edited.
- A transparent markup overlay is also supported on GPT Image 2.5 and 2.6, but cannot be combined with `mask`.
- Do not use `input_fidelity` with GPT Image 2.x; the documented high/low control applies to GPT Image 1.5 (and low-only for 1-mini).
- Mask-based image editing remains generative and prompt-guided. The API's mask is not a hard pixel lock. Keep the original protected pixels and verify output differences deterministically.

Official API reference:
https://developers.openai.com/api/reference/go/resources/images/methods/edit

### SAM 3.1 prompt rules
- A request uses either one short concept/noun-phrase prompt OR box/point prompts, not both in the same prompt.
- For Thiri's already-known garment regions, box/point prompts are likely more controllable than generic text prompts.
- Use one garment layer per request: blouse, longyi, drape, then trims. A concept prompt can return every matching instance, so broad concepts may capture neighboring fragments.
- SAM output masks are geometry for measuring/cropping/compositing; they do not perform garment fitting or decide cultural/design correctness.

Official prompt guide:
https://dev.meta.ai/docs/sam/segmenting

## 8. MLCW Run #35 implementation settings

| Setting | Decision |
|---|---|
| Candidate edit model | GPT Image 2.5 supported edit variant |
| Background | Transparent PNG requested for isolated clean-base output |
| Input references | Original Thiri + approved reconstruction candidate |
| Protected region | Face, eyes, hair/bun, white flower, earrings, visible skin and hands |
| Reconstruction region | Clothing-covered torso/arms/waist/legs only where required for a modest neutral base |
| Mask size | Exactly same canvas as first input; PNG <4 MB |
| Segmentation | SAM 3.1 box/point prompts per garment layer |
| Composite | Deterministic alpha compositing |
| Acceptance | Pixel diff + human review; generated pixels labelled separately |

## 9. Current hold point — unchanged

The user has not yet visually approved the generated neutral-base candidate as the Master Base. Therefore:
- Do not create final alpha matte or declare base approved.
- Do not start P01 garment fitting/compositing.
- Do not claim identity preservation or QA pass.
- Next action is visual approval/revision of the existing candidate.


## 10. Official documentation verification (2026-11-01)

### GPT Image 2.5 edit API

The current OpenAI API reference lists GPT Image 2.5 variants including `gpt-image-2.5-sunburst` and `gpt-image-2.5-flare`.
- Up to 16 input images may be supplied.
- Transparent background is supported on these GPT Image 2.5 variants; PNG or WebP output is required to retain alpha.
- A mask is a PNG under 4 MB, must match the first input image dimensions, and uses fully transparent pixels to identify the editable area.
- Transparent markup guidance is supported on GPT Image 2.5/2.6 but cannot be combined with a mask.
- `input_fidelity` is documented for GPT Image 1.5; omit it for GPT Image 2.x.
- Mask-based edits are prompt-guided and may not follow the mask boundary exactly.

Sources:
- https://developers.openai.com/api/reference/go/resources/images/methods/edit
- https://developers.openai.com/api/docs/guides/image-generation
- https://developers.openai.com/api/docs/guides/image-prompting

### SAM 3.1 prompt and parser details

Official Meta docs specify:
- Concept prompt: one short noun phrase per request (e.g. "red blouse"); no multi-concept comma/and list.
- Or use box/point prompts when the target object is already localized. Do not mix concept and box/point prompts in the same prompt.
- SAM 3.1 returns a box and mask for each matched object. Masks can be measured, cropped and composited.
- Meta provides official parser libraries, including Python `meta_sam_parser` and TypeScript `@meta-sam/parser`, for decoding the output mask grammar.

Sources:
- https://dev.meta.ai/docs/sam/segmenting
- https://dev.meta.ai/docs/sam/overview
- https://dev.meta.ai/docs/sam/client-libraries

### MLCW decision

For P01, use separate segmentation requests for blouse, ruby longyi and gold/cream drape, or use localized box/point prompts. Do not send a combined prompt like "blouse, longyi and shawl". Treat model masks as candidate geometry; human-reviewed masks and deterministic pixel QA remain the acceptance authority.
