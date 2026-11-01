# MLCW V1.0.8 — Run #37 Glow Suppression Alpha Candidate

**Date:** 2026-11-01  
**Status:** Derived diagnostic candidate; human silhouette and identity approval pending.

## Input
- Run #36 native transparent candidate B.
- Dimensions: 1024×1536 RGBA.
- Input alpha range: 0–254.
- Input SHA-256: `602651a43e5fa1658b43a39a4d3dd77aa7cf9a4a67d5ab1736ed3160a44d4011`.

## Actual local pixel processing
The input had a broad low-alpha dark glow. Rather than globally boosting alpha, a foreground matte was derived from the connected alpha region using threshold `alpha > 10`; this isolates the main connected subject from the diffuse low-alpha glow. A signed-distance transition over 3 pixels was applied to create anti-aliased silhouette edges. RGB channels were retained from the generated input; only alpha was replaced.

This is deterministic local post-processing, not a new GPT Image API call and not SAM inference.

## Output
- File: `Thiri_CandidateB_GlowSuppressed_Alpha.png`
- Dimensions: 1024×1536 RGBA.
- Alpha min/max: 0/255.
- Fully transparent: 1,191,336 pixels.
- Partially transparent: 15,235 pixels.
- Fully opaque: 366,293 pixels.
- SHA-256: `e78e451a467c23bbf38d5b1701d8f8837d973dd58bb214cf9202f1e0749d50da`.

## Visual QA previews
Composited on white, dark and saturated magenta backgrounds. The diffuse halo is substantially suppressed and the subject silhouette remains visible. Fine edge inspection is still required at 100–200% for hair wisps, flower petals, earring loops, finger gaps, skirt hem and feet.

## Saved Library assets
- `/My Little Creative World/Run 36/Thiri_CandidateB_GlowSuppressed_Alpha.png`
- `/My Little Creative World/Run 36/CandidateB_White_Background_QA.jpg`
- `/My Little Creative World/Run 36/CandidateB_Dark_Background_QA.jpg`
- `/My Little Creative World/Run 36/CandidateB_Saturated_Background_QA.jpg`

## Limitations
- Generated reconstruction pixels are not original source pixels.
- Alpha matte is threshold-derived and may omit very faint hair/edge pixels.
- No comparison has yet established face/eye/hair/flower/earring identity similarity against canonical original.
- No P01 garment segmentation, compositing or protected-region QA has been performed.

**Decision:** alpha-cleanup candidate technically generated; visual silhouette review PENDING; Master Base NOT APPROVED; P01 composite NOT RUN.
