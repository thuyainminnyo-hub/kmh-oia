# MLCW V1.0.8 — Run #40 Original Head Preservation Prototype

**Date:** 2026-11-01  
**Status:** Prototype composite generated; review pending; not production-approved.

## Purpose
Preserve original Thiri head/face/hair/flower/earring pixels from canonical reference `15309(1).png`, and use the generated neutral-base candidate only for the reconstructed body.

## Inputs
- Canonical source: `15309(1).png`, 1024×1536 RGBA.
- Reconstructed body source: `MLCW_Run36_CandidateB_GlowSuppressed.png`, 1024×1536 RGBA.

## Method
1. Identify border-connected near-white background in the canonical source.
2. Derive a protected head mask for face, eyes, hair bun, flower, earrings, side hair strands and visible neck skin.
3. Exclude original cream collar pixels from the lower neck mask using a constrained skin-color mask.
4. Remove the generated candidate's head region while retaining generated body/neutral garment.
5. Deterministically alpha-composite the original protected head over the reconstructed body.
6. Apply a 1.2-pixel edge feather on the derived head matte to reduce jagged cutout edges.

This is a derived mask plus deterministic composite; it is not an AI full-character redraw, and it does not reconstruct exact hidden source pixels.

## Actual measurement
- Protected-head mask bounding box: `[358,24,641,420]`.
- Protected mask nonzero pixels: 82,611.
- Fully opaque protected-head core: 81,164 pixels.
- Exact source RGB matches in that fully opaque core: 81,164 / 81,164 = **100%**.
- Output canvas: 1024×1536 RGBA.
- Output alpha: min 0, max 255.
- Transparent pixels: 1,192,863.
- Partial-alpha pixels: 12,247.
- Fully opaque pixels: 367,754.
- Output SHA-256: `330adfac9dd94a186bf35b6c027789369de94607b901ee79ef075431d540db4c`.

The 100% figure applies only to the fully opaque pixels inside the defined protected-head core mask. It does not describe body pixels, feathered boundary pixels or overall visual identity.

## Output files saved to Library
- `/My Little Creative World/Run 40/Thiri_Original_Head_Preserved_Reconstructed_Body_v4.png`
- `/My Little Creative World/Run 40/Full_Canvas_Checker_Preview.jpg`
- `/My Little Creative World/Run 40/Head_Neck_Seam_Inspection.jpg`
- `/My Little Creative World/Run 40/Protected_Head_Mask.png`
- `/My Little Creative World/Run 40/Original_vs_Reconstructed_Provenance_Map.jpg`
- `/My Little Creative World/Run 40/Original_vs_Candidate_Comparison.jpg`
- `/My Little Creative World/Run 40/Head_Preservation_Metrics.json`

## Research constraints

- OpenAI image edit masks are prompt-guidance rather than hard pixel locks; retain deterministic comparison after generative edits.
- GPT Image 2.5 supports up to 16 inputs and transparent output; mask must be a same-size PNG under 4MB.
- SAM 3.1 can return concept- or box/point-prompted masks, and Meta parser libraries decode those outputs. SAM masks are segmentation candidates, not final fit/identity approval.

Official sources:
- OpenAI Image Edit API: https://developers.openai.com/api/reference/go/resources/images/methods/edit
- OpenAI Image Generation Guide: https://developers.openai.com/api/docs/guides/image-generation
- Meta SAM 3.1 segmentation prompts: https://dev.meta.ai/docs/sam/segmenting
- Meta SAM parser libraries: https://dev.meta.ai/docs/sam/client-libraries

## Gate decision
- Original head pixel copy (opaque core): PASS (81,164/81,164 exact RGB match).
- Head matte boundary: derived; human review pending.
- Neck seam: improved and visually inspected; human approval pending.
- Generated body proportions: not verified against original because body was occluded by cream clothing.
- Master Base approval: PENDING.
- P01 segmentation/composite: NOT RUN.
- Production release: HOLD.

## Next
Human review this prototype, especially neck seam, earrings, hair strands and body/shoulder proportions. If accepted, lock this as a reconstruction working base, then prepare P01 blouse/longyi/drape layers. Do not label reconstructed pixels as original source pixels.
