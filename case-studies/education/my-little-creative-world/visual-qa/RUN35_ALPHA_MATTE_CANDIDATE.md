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
