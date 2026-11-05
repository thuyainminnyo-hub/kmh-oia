# MLCW Run #35 — Alpha Matte Candidate Inspection

**Date:** 2026-11-01  
**Status:** Diagnostic candidate generated; Master Base visual approval still pending.

## Input

- Source: `a_clean_full_body_illustration_of_the_same_young_c.png`
- Source dimensions: 1024×1536
- Source mode: RGB
- SHA-256: `361f18a1c2046acc4c9bf90740a3a398923c735f79852d1fabaed63de0de8633`
- Background: near-white, RGB raster; no alpha channel.

## Method

A non-generative, local alpha-matte candidate was extracted using:
1. Identify near-white pixels (minimum RGB channel >= 238, channel spread <= 22).
2. Keep only near-white pixels connected to the canvas boundary as background.
3. Preserve enclosed white details (e.g. the flower and eye highlights) as subject pixels.
4. Create a 4px signed-distance feather at the silhouette edge.
5. Estimate foreground edge colors against a white matte and export RGBA PNG.

This is a diagnostic extraction method. It is not equivalent to SAM segmentation, and its boundary has not yet been human-approved.

## Verified output facts

- Output: `MLCW_Run35_Thiri_Clean_Base_Alpha_Candidate.png`
- Dimensions: 1024×1536
- Mode: RGBA
- Alpha min/max: 0 / 255
- Four canvas edges and all four corners: alpha = 0
- Fully transparent pixels: 1,192,397 (75.811%)
- Partially transparent pixels: 14,523
- Fully opaque pixels: 365,944
- Subject bounding box (x1,y1,x2,y2): `[135,23,883,1501]`
- Output SHA-256: `1f07eb1b3ec43407e8bc4fa460ebf0eb51e4f32744696e270db8f455c6de09a9`

## Outputs saved to Library

- `/My Little Creative World/Run 35/Thiri_Clean_Base_Alpha_Candidate.png`
- `/My Little Creative World/Run 35/Thiri_Alpha_Matte_Preview.png`
- `/My Little Creative World/Run 35/Alpha_Matte_Inspection.json`

## Evidence boundary

- Alpha channel existence, dimensions, edge transparency and pixel counts were programmatically inspected.
- Candidate is generated artwork; no original face/hair/earring pixels were preserved by this generation step.
- Alpha matte is a derived mask from the generated white-background candidate, not a SAM output.
- No identity similarity score, P01 layer segmentation, P01 composite or protected-region pixel QA has been performed.

## Decision

**Transparency preparation: TECHNICAL CHECK PASS (candidate only).**  
**Visual silhouette approval: PENDING.**  
**Master Base approval: PENDING USER REVIEW.**  
**P01 compositing: NOT RUN.**

Next gate: review the checkerboard preview for halos, missing hair strands, flower details, earrings, finger gaps, feet and skirt edge. After approval, separately review the reconstructed identity features against the canonical reference. Only then can the alpha candidate be promoted to the working base.


## Official documentation cross-check (2026-11-01)

- OpenAI's current Image Generation guide recommends requesting a transparent background and preserving the returned PNG/WebP alpha channel; it explicitly warns that a drawn checkerboard is not transparency.
- OpenAI's Image Edit reference says GPT Image 2.5 Sunburst is the precision-oriented editing choice, while Flare is faster everyday generation. Transparent backgrounds are supported on the documented 2.5 variants.
- SAM 3.1's parser libraries decode the model's output grammar into binary raster masks; that is separate from creating the subject alpha matte from this local candidate.

Sources:
- https://developers.openai.com/api/docs/guides/image-prompting
- https://developers.openai.com/api/docs/guides/image-generation
- https://developers.openai.com/api/reference/resources/images/methods/edit
- https://dev.meta.ai/docs/sam/client-libraries

## Output preview artifacts

- Alpha PNG saved to the persistent user Library at `/My Little Creative World/Run 35/Thiri_Clean_Base_Alpha_Candidate.png`.
- Checkerboard inspection preview saved at `/My Little Creative World/Run 35/Thiri_Alpha_Matte_Preview.png`.
- Alpha inspection JSON saved at `/My Little Creative World/Run 35/Alpha_Matte_Inspection.json`.
- The RGBA PNG passed technical checks for canvas size, alpha range, transparent four edges and transparent corners. Human silhouette review is still required.


## 2nd official-doc review — preferred next iteration

OpenAI's current image-prompting guide provides a more suitable path than deriving alpha from a white matte: request a transparent-background image edit, explicitly ask for an isolated subject and clean alpha edges, use PNG/WebP, and preserve the returned alpha channel. A drawn checkerboard is not transparency. This is the preferred next candidate workflow, but output still needs inspection for halos and silhouette damage.

The current local alpha-matte candidate remains useful as a diagnostic fallback. Because it was extracted from RGB-on-white, edge pixels may carry white-matte contamination despite feathering. Do not promote it to production merely because the alpha channel exists.

For SAM 3.1, the official Python parser can decode the model mask to a row-major binary raster of exactly width × height, or COCO RLE for storage/evaluation. The parser only decodes output; the application remains responsible for sending the API request and verifying completion status. This makes a reproducible mask QA pipeline possible.

### Updated decision
1. Keep current alpha candidate as **TECHNICAL PREVIEW ONLY**.
2. Preferred next alpha candidate: GPT Image 2.5 Sunburst edit with transparent background and explicit no-restyle/no-halo prompt.
3. Independently compare output silhouette and protected features; generated output is not an exact original-pixel preservation method.
4. SAM 3.1 mask output can be decoded to binary raster; human review and pixel-diff QA remain mandatory.

Sources:
- OpenAI image prompting / transparent cutout: https://developers.openai.com/api/docs/guides/image-prompting
- OpenAI image edit API: https://developers.openai.com/api/reference/resources/images/methods/edit
- Meta SAM parser: https://dev.meta.ai/docs/sam/client-libraries


## Official documentation refresh — Run #36 preparation (2026-11-01)

OpenAI's current prompting guide gives a concrete transparent-cutout recipe:
- Request an isolated subject in the prompt and set `background="transparent"`.
- Preserve the returned PNG/WebP alpha channel; omit `output_compression` for PNG.
- Explicitly ask for a crisp silhouette and no halos/fringing, and prohibit solid backdrops, checkerboards, scenery and shadows.
- Repeat the transparent-background requirement in subsequent edits.

The Image Edit API confirms GPT Image 2.5 Sunburst and Flare support transparent output, up to 16 input images, and masks/markup with documented constraints. For the MLCW precision-oriented extraction test, use Sunburst as the first candidate; keep the existing locally-derived alpha as a baseline for comparison, not as a production-approved matte.

Meta SAM 3.1 documentation confirms it returns boxes and masks for measuring, cropping or compositing. Its parser packages decode the output stream into usable mask structures. This is the correct role for SAM in MLCW: garment-region segmentation, not background alpha generation or identity preservation.

### Run #36 controlled comparison protocol
1. Candidate A: current white-matte-derived RGBA.
2. Candidate B: native transparent GPT Image 2.5 Sunburst edit of the same approved source.
3. Composite both over light, dark and saturated checker-free backgrounds.
4. Inspect hair wisps, flower petals, earring loops, fingers, skirt hem and foot contours at 100% and 200%.
5. Calculate alpha edge coverage, isolated fringe/halo indicators and connected-component anomalies; keep human review mandatory.
6. Compare visible identity features to the canonical Thiri reference; generated pixels remain labelled reconstructed.
7. Do not promote either candidate until user visually approves the silhouette and identity.

### Official sources
- OpenAI transparent cutout prompting: https://developers.openai.com/api/docs/guides/image-prompting
- OpenAI image edit API: https://developers.openai.com/api/reference/resources/images/methods/edit
- OpenAI image generation: https://developers.openai.com/api/docs/guides/image-generation
- Meta SAM 3.1 overview: https://dev.meta.ai/docs/sam/overview
- Meta SAM parser libraries: https://dev.meta.ai/docs/sam/client-libraries

**Current gate unchanged:** native transparent candidate has not been generated; current alpha remains technical preview; user visual approval pending; P01 segmentation/composite not run.


## Run #36 — Official source validation and execution readiness

### OpenAI transparent edit — verified API parameters
The official image prompting guide's transparent-cutout example specifies:
- `model="gpt-image-2.5-sunburst"`
- `size="1024x1536"`
- `quality="medium"`
- `background="transparent"`
- `output_format="png"`
- Omit `output_compression` for PNG and preserve the returned alpha bytes.

The edit API confirms 1024×1536 is a supported standard size; arbitrary resolutions are supported when dimensions are divisible by 16 and aspect ratio is between 1:3 and 3:1. The Thiri canvas already meets the standard size requirement.

Important: this API workflow requires an actual Images Edit API request and returned image bytes. A prompt description or a generated mockup is not evidence that this API call happened. No such API call has been made for MLCW Run #36 yet.

### SAM 3.1 — segmentation decision
Meta's official docs say a concept prompt returns a box and mask for every matching instance. If the target is already located, box/point prompts can target the specific object. For the multi-part P01 sheet, use separately localized boxes/points for blouse, longyi and drape rather than a broad phrase that might capture neighboring garments.

### Run #36 controlled test
- Baseline A: existing white-matte alpha PNG.
- Candidate B: native transparent GPT Image 2.5 Sunburst edit (awaiting actual API execution).
- Compare on light, dark and saturated backgrounds.
- Inspect at 100% and 200% around hair, flower, earrings, fingers, skirt hem and feet.
- Keep generated/reconstructed pixels marked separately from source pixels.
- No Master Base promotion until user reviews and approves the candidate.

### Official references
- OpenAI transparent cutout prompt and settings: https://developers.openai.com/api/docs/guides/image-prompting
- OpenAI Image Edit API: https://developers.openai.com/api/reference/go/resources/images/methods/edit
- Meta SAM prompt segmentation: https://dev.meta.ai/docs/sam/segmenting
- Meta SAM overview: https://dev.meta.ai/docs/sam/overview
