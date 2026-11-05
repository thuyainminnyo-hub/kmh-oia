# MLCW V1.0.8 — Run #36 Native Transparent Candidate Inspection

**Date:** 2026-11-01  
**Candidate:** B — native RGBA image-generation output  
**Decision:** HOLD — not a clean production cutout.

## Source facts
- Dimensions: 1024 × 1536
- Mode: RGBA
- Alpha range: 0–254
- Alpha = 0: 1,171,319 pixels (74.470%)
- Partial alpha (1–254): 401,545 pixels (25.530%)
- Fully opaque alpha = 255: 0 pixels (0%)
- SHA-256: `602651a43e5fa1658b43a39a4d3dd77aa7cf9a4a67d5ab1736ed3160a44d4011`

## Visual/technical finding
The image contains a dark soft glow/vignette around the character. Although an alpha channel exists and the corners are transparent, the nonzero alpha glow occupies a broad region and no pixel reaches fully opaque alpha. The output is therefore not a clean isolated character cutout. The halo/glow can contaminate composites and lower opacity of the subject. Do not promote to Master Base.

## Saved artifacts in user Library
- `/My Little Creative World/Run 36/Thiri_Native_Transparent_Candidate_B.png`
- `/My Little Creative World/Run 36/Native_Transparent_Checker_Preview.jpg`
- `/My Little Creative World/Run 36/Native_Transparent_Light_Preview.jpg`
- `/My Little Creative World/Run 36/Native_Transparent_Dark_Preview.jpg`
- `/My Little Creative World/Run 36/Native_Transparent_Saturated_Preview.jpg`
- `/My Little Creative World/Run 36/Native_Transparent_Inspection.json`

## Candidate comparison
- Candidate A: white-matte-derived alpha — technical preview, edge matte risk.
- Candidate B: native RGBA generation — alpha present, but diffuse glow and no fully opaque pixels; not suitable as production cutout.
- Both remain unapproved.

## Next iteration
Generate an isolated subject with no glow, aura, vignette, shadow, backdrop or environmental lighting; require a crisp, opaque subject body with alpha reserved for exterior anti-aliased edges only. If the generator continues producing a glow, use a dedicated segmentation/matting workflow and human-correct the mask. Review the new result on white, black and saturated backgrounds before approval.

## Evidence boundary
- Alpha statistics were measured from the actual PNG bytes using local pixel inspection.
- No exact original-pixel identity preservation is claimed.
- No P01 segmentation, compositing or protected-region pixel QA has been run.
- The candidate is newly generated reconstruction artwork, not an edit preserving original pixels.

**Run #36 result:** native alpha channel technically exists; silhouette quality FAIL/HOLD; Master Base approval pending; P01 composite not run.


## Official documentation findings — next iteration

OpenAI's official transparent-cutout example recommends:
- Supply the source image to the Image Edit API.
- Set `background="transparent"`, `output_format="png"`, and use the supported GPT Image 2.5 model.
- Request an isolated subject with a crisp silhouette and no halos/fringing, solid backdrop, checkerboard, scenery or shadow.
- Preserve the returned PNG alpha channel; do not re-encode it as JPEG or flatten it.

Official guide: https://developers.openai.com/api/docs/guides/image-prompting

OpenAI's Image Generation guide confirms transparent backgrounds for GPT Image 2.5 Sunburst and Flare and recommends PNG or WebP to retain alpha. Supported quality levels include high/xhigh/max; final candidate quality should be compared against generation cost and latency. Official guide: https://developers.openai.com/api/docs/guides/image-generation

Meta SAM 3.1 returns a box and mask for every matching concept instance, or segments specific objects from box/point prompts. For P01's small crowded concept panel, localized box/point prompts are safer than broad text-only prompts. It returns geometry for cropping/compositing; it does not fit the garment to Thiri. Official guide: https://dev.meta.ai/docs/sam/segmenting

## Run #37 decision proposal

Do not try to repair Candidate B by globally increasing alpha: that would also make the diffuse glow opaque. Instead:
1. Re-run a true source-image edit using the original reference and approved neutral reconstruction, with native transparent output and no aura/glow/shadow.
2. If the output still contains a diffuse alpha field, reject it and use a dedicated foreground segmentation/matting workflow with human correction.
3. Keep protected identity features under human review; no generated image is assumed to preserve original pixels.
4. Only after an approved clean base, segment P01 blouse, ruby longyi and drape with separate localized masks.

**Status:** Candidate B remains rejected for production. Native transparent edit via documented API has not been executed as a separate API request in this workflow. No P01 segmentation/composite has run.
