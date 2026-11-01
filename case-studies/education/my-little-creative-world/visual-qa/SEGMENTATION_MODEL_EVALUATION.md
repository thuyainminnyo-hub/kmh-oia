# MLCW Run #32 — Segmentation Model Evaluation (updated 2026-11-01)

## Decision summary

Use a promptable, human-reviewed segmentation workflow:
1. Generate candidate masks with text, exemplar, point and box prompts.
2. Refine boundaries with follow-up positive/negative prompts.
3. Human reviewer corrects masks and labels protected regions.
4. Deterministic pixel QA validates the final composite.

Do not auto-promote model masks directly to production.

## Candidate A — Meta SAM 3.1

- SAM 3 accepts open-vocabulary text prompts, image exemplars, points, boxes and masks to segment objects in still images and video.
- SAM 3.1 checkpoints were announced on 2026-03-27. The headline 3.1 update is Object Multiplex and faster multi-object video tracking; do not infer that it improves Thiri's single-image clothing segmentation without testing.
- Recommended role: primary promptable segmentation candidate for the stylized Thiri artwork. Test short noun prompts and exemplar/point/box prompts for the gold blouse, red patterned longyi and cream-gold shawl separately.
- Self-hosted upstream setup currently calls for Python 3.12+, PyTorch 2.7+ and CUDA-compatible GPU with CUDA 12.6+; SAM 3.1 checkpoints require the current upstream code.
- Meta Model API also exposes a hosted `sam-3.1` segmentation endpoint; pricing displayed by Meta is $2.50 per 1,000 still images. API use requires authorized credentials and separate cost approval.
- License: Meta SAM License (custom terms, not Apache 2.0). Review redistribution, use and commercial terms before product integration.

## Candidate B — FASHN Human Parser

- SegFormer-B4 fine-tuned for fashion/human parsing.
- 18 semantic classes including face, hair, top, dress, skirt, pants, arms, hands, legs, torso and jewelry.
- Documented input size: 384 x 576. Resizing its mask back to 1024 x 1536 cannot recover detail lost during downsampling.
- Useful as a semantic baseline for face/hair/clothing/accessory masks.
- Limitation: optimized for single-person, clearly visible fashion/e-commerce imagery; MLCW Thiri is stylized/chibi artwork, so domain suitability must be benchmarked.
- License: NVIDIA Source Code License for SegFormer. Legal review required before commercial use.

## MLCW recommendation

Benchmark SAM 3.1 prompts against FASHN as a semantic baseline on the same human-reviewed masks:
- annotate face, hair/flower, jewelry, arms/hands, blouse, longyi and drape separately;
- measure per-class IoU and boundary F-score;
- preserve source pixels in protected regions;
- use human correction for small accessories, occlusion and transparent drape;
- store hashes, dimensions, model/checkpoint version, prompts, raw/corrected masks, output and QA JSON.

## Run #33 source-asset findings

- Canonical Thiri reference: `15309(1).png`, 1024x1536 RGBA, 0% transparent. It still shows the cream blouse and longyi; it is not a clean body base.
- P01 source panel: `15312(1).png`, 225x431 RGBA, 36.346% transparent, 75 connected alpha components. Largest component: 59,523 px (96.428% of opaque pixels), bbox `[0,18,189,431]`, touches left and bottom edges. Second largest component: 1,875 px at bbox `[194,85,225,205]` (adjacent purple fragment).
- All ten outfit panels' largest alpha components touch the left and bottom edges. P02, P05 and P10 have substantial second components.
- Accessory strip: `15304(1).png`, 1536x169 RGB, opaque, requiring object-level segmentation and transparent exports.
- P01-P10 are working slots; do not assume they map to legacy `MLCW-OUTFIT-001..010` identifiers by sequence.

## Gate

**Asset intake: PASS (12 assets inspected).**  
**Production visual readiness: HOLD.** Need an approved clean Thiri body base and complete uncropped P01 garment layers before reliable compositing. No actual model inference or P01 composite has been run.
