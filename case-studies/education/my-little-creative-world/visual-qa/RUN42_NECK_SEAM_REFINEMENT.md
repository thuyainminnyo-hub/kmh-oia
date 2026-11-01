# MLCW V1.0.8 — Run #42 Neck Seam Refinement v5

**Date:** 2026-11-01  
**Status:** Refined prototype generated; human review pending; Master Base HOLD.

## Work performed
Run #40 v4 showed a visible lower-neck transition where the original preserved head/neck met the reconstructed neutral-body candidate. Run #42 applies a deterministic taper to the lower-centre portion of the original head mask while keeping the side zones (where hair strands and earrings hang) protected.

Parameters:
- Vertical fade starts at y=378 and reaches zero at y=412.
- Horizontal smooth taper from x=398 to x=420 and x=598 to x=620.
- Fully tapered central region: x=420..598.
- Original face, eyes, hair bun, flower and earrings above the transition remain unchanged.

This is deterministic alpha compositing, not a generative edit.

## Actual pixel verification
- New fully opaque protected core: 78,452 pixels.
- Exact source RGB matches: 78,452 / 78,452.
- Changed pixels inside opaque core: 0.
- Exact match ratio: 100% within this new opaque core.
- Partially transparent head-mask pixels: 3,845.
- RGB differences within partial head-mask pixels: 3,044 (expected edge blending).
- Full output: 1024×1536 RGBA.
- Alpha zero: 1,190,208 pixels.
- Partial alpha: 13,885 pixels.
- Alpha 255: 368,771 pixels.
- Output SHA-256: `1b73c6fe80edac5e013f959452881d768f9da715450894ab673931c2c8f28ae8`.

The 100% match applies only to the fully opaque core. It does not apply to feathered pixels or reconstructed body.

## Output artifacts in Library
- `/My Little Creative World/Run 42/Thiri_Neck_Seam_Refined_v5.png`
- `/My Little Creative World/Run 42/Full_Checker_Preview_v5.jpg`
- `/My Little Creative World/Run 42/Neck_Seam_200pct_v5.jpg`
- `/My Little Creative World/Run 42/Protected_Head_Mask_v5.png`
- `/My Little Creative World/Run 42/White_Background_Preview.jpg`
- `/My Little Creative World/Run 42/Dark_Background_Preview.jpg`
- `/My Little Creative World/Run 42/Magenta_Background_Preview.jpg`
- `/My Little Creative World/Run 42/Neck_Seam_Refined_Metrics.json`

## Code and tests
- `neck_seam_refinement.py` — deterministic lower-neck mask taper.
- `test_neck_seam_refinement.py` — tests unchanged upper head, tapered lower centre, protected side zones, and invalid input rejection.

## Research findings
- OpenAI Image Edit API: masks guide the edit but do not guarantee exact shape adherence; transparent output requires PNG/WebP. The API's current edit models support image/mask workflows; GPT Image 2.5 can also use transparent markup guidance. See https://developers.openai.com/api/reference/resources/images/methods/edit
- OpenAI Image Prompting: explicitly request transparent background and inspect decoded alpha; a drawn checkerboard is not transparency. See https://developers.openai.com/api/docs/guides/image-prompting
- Meta SAM 3.1: choose either concept noun phrase or localized box/point prompts, not both in one request. See https://dev.meta.ai/docs/sam/segmenting
- Meta SAM returns object masks useful for measuring, cropping and compositing, not visual approval by itself. See https://dev.meta.ai/docs/sam/overview

## Gate
- Refined neck transition: prototype generated; visual review pending.
- Protected opaque head core: exact RGB PASS (78,452/78,452).
- Side hair/earring preservation: core remains protected; fine boundary review pending.
- Body proportions: not approved.
- Master Base: HOLD.
- P01 outfit composite: NOT RUN.
