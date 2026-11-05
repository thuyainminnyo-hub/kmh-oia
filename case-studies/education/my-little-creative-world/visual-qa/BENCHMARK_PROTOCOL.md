# MLCW Segmentation Benchmark Protocol

## Purpose

Compare promptable segmentation and semantic-parser masks against human-reviewed reference masks for stylized Thiri. This evaluates segmentation quality; it does not by itself validate character likeness or outfit quality.

## Reference-mask preparation

Create separate binary PNGs at source-image dimensions for:
- face
- hair (split bun and flower ornament if required)
- jewelry / accessories
- arms and hands
- upper garment
- longyi / skirt
- drape / shawl

Rules:
1. Never resize source and masks independently. If the model requires resizing, map output back using a documented inverse transform.
2. Keep regions separate; allow overlap only when the annotation guide defines it.
3. Have a second reviewer inspect reference masks and resolve disagreements.
4. Record source SHA-256, dimensions, color mode, annotator, review date and annotation-guide version.

## Model comparison

Run both candidates against the same source and reviewed masks:
- SAM 3.1: concept/text prompt, exemplar prompt, and positive/negative point or box refinement.
- FASHN Human Parser: raw semantic masks for relevant face, hair, top, skirt and jewelry labels.
- Final human-corrected masks.
- Reviewed reference masks.

Per region compute:
- IoU = TP / (TP + FP + FN)
- Boundary F-score with tolerance stated in original-image pixels
- False-positive and false-negative pixel counts
- Inference time and manual correction time

Report every class separately; a strong outfit score must not hide poor face/hair segmentation. Visual approval remains mandatory.

## Current source readiness (Run #33)

- Canonical Thiri reference `15309(1).png` is fully opaque and still shows the cream outfit; hidden body regions do not exist in the source.
- P01 panel `15312(1).png` has alpha, but the largest component is clipped at the left/bottom edges and a neighboring purple fragment is present.
- All ten outfit panels have edge-touching largest components; several contain substantial neighboring artwork.
- Accessories strip `15304(1).png` is opaque RGB and must be segmented into separate transparent assets.
- P01-P10 working slots have not yet been reconciled with the legacy asset IDs MLCW-OUTFIT-001..010.

A separate approved clean body base and complete uncropped P01 garment layers are required before a trustworthy visual benchmark.

## Synthetic test evidence

GitHub Actions Visual Pixel QA run #7 passed 9 synthetic tests (4 segmentation metric tests + 5 pixel QA tests). This validates the metric/QA code, not actual Thiri model predictions.

## Result template

| Region | Model | IoU | Boundary F-score | FP pixels | FN pixels | Manual review | Decision |
|---|---|---:|---:|---:|---:|---|---|
| Face | SAM 3.1 / FASHN / corrected | — | — | — | — | Pending | Not tested |
| Hair / flower | SAM 3.1 / FASHN / corrected | — | — | — | — | Pending | Not tested |
| Upper garment | SAM 3.1 / FASHN / corrected | — | — | — | — | Pending | Not tested |
| Longyi / skirt | SAM 3.1 / FASHN / corrected | — | — | — | — | Pending | Not tested |
| Drape / shawl | SAM 3.1 / corrected | — | — | — | — | Pending | Not tested |
