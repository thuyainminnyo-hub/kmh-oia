# MLCW Segmentation Benchmark Protocol

## Purpose

Compare proposed semantic-parser and prompt-refined masks against human-reviewed reference masks for the stylized Thiri character. The benchmark evaluates segmentation masks; it does not by itself validate character likeness or outfit quality.

## Reference-mask preparation

Create a separate binary PNG at the original source-image dimensions for each region:
- face
- hair (include bun and flower separately if the QA plan needs accessory-specific control)
- jewelry / accessories
- arms and hands
- upper garment
- longyi / skirt
- drape / shawl (custom class; do not assume the generic fashion parser has this class)

Rules:
1. Never resize the source image and masks independently. If a model requires resizing, map its output back to original image dimensions using a documented inverse transform.
2. Keep each region as an individual binary mask; allow explicit overlap only when the annotation guide defines it.
3. Have a second reviewer inspect the reference masks and resolve disagreements before benchmarking.
4. Preserve the original source asset and record its SHA-256, dimensions and color mode.
5. Record annotator, review date and annotation-guide version.

## Model comparison

For every region, retain:
- FASHN Human Parser raw predicted class mask (when applicable)
- SAM 2.1 prompt-refined mask and positive/negative prompts
- final human-corrected mask
- reference mask
- model/checkpoint, package and preprocessing versions

Compute:
- Intersection over Union (IoU) per region
- Boundary F-score per region, with tolerance stated in original-image pixels
- false-positive and false-negative pixel counts
- processing time and any manual correction time

IoU is TP / (TP + FP + FN). Boundary F-score compares predicted and reference contours within a stated pixel tolerance. Do not compare models using visually attractive overlays alone.

## Acceptance policy

- Do not establish a universal numeric pass threshold before the first representative Thiri benchmark is annotated and reviewed.
- Compare models on the exact same original image, reference masks, image dimensions and evaluation settings.
- Record every class result, not only a mean score; an excellent outfit score must not hide a failed face/hair mask.
- A human reviewer must approve identity/accessory masks and garment boundaries.
- Pixel QA on the final composite remains a separate gate: target coverage, uncovered target pixels, protected-region changes and spillover.

## Current evidence

- Segmentation-metric unit tests: 4 passed in GitHub Actions Visual Pixel QA run #7.
- Pixel QA harness unit tests: 5 passed in the same run.
- Total: 9 passed, 0 failed.
- These are synthetic unit tests. No real Thiri/P01 model prediction or human reference mask has been benchmarked yet.
- Real benchmark remains blocked until the full-resolution original Thiri image and clean P01 source/layers can be used to create reviewed masks.

## Result template

| Region | Model | IoU | Boundary F-score | FP pixels | FN pixels | Manual review | Decision |
|---|---|---:|---:|---:|---:|---|---|
| Face | FASHN / SAM 2.1 / corrected | — | — | — | — | Pending | Not tested |
| Hair | FASHN / SAM 2.1 / corrected | — | — | — | — | Pending | Not tested |
| Upper garment | FASHN / SAM 2.1 / corrected | — | — | — | — | Pending | Not tested |
| Longyi / skirt | FASHN / SAM 2.1 / corrected | — | — | — | — | Pending | Not tested |
| Drape / shawl | SAM 2.1 / corrected | — | — | — | — | Pending | Not tested |
