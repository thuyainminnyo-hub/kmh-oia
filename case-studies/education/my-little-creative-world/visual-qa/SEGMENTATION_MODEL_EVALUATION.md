# MLCW Run #32 — Segmentation Model Evaluation

Date: 2026-11-01

## Decision summary

Use a two-stage, human-reviewed segmentation workflow:
1. Semantic human parser proposes classes and approximate regions.
2. Promptable segmentation refines boundaries from positive/negative points or boxes.
3. Human reviewer corrects the masks.
4. Deterministic pixel QA validates the final composite.

Do not auto-promote model masks directly to production.

## Candidate A — FASHN Human Parser

- Model: SegFormer-B4 fine-tuned for fashion/human parsing.
- Output: 18 semantic classes: background, face, hair, top, dress, skirt, pants, belt, bag, hat, scarf, glasses, arms, hands, legs, feet, torso, jewelry.
- Documented input size: 384 x 576.
- Useful for initial face/hair/clothing/accessory mask proposals.
- Important limitation: model card says it is optimized for single-person images with clear visibility and fashion/e-commerce imagery. MLCW Thiri is stylized/cartoon artwork, so domain suitability must be tested; class confusion is possible.
- License: NVIDIA Source Code License for SegFormer. Legal review required before commercial use.

## Candidate B — Meta SAM 2.1

- Promptable image segmentation using point/box/mask prompts; supports automatic mask generation.
- Use for refining manually selected garment boundaries, not semantic classification of clothing types.
- Upstream install guidance: Linux, Python >=3.10, PyTorch >=2.5.1 and matching torchvision; CUDA recommended for normal GPU setup.
- Model/checkpoint/demo/training code license is Apache 2.0 according to upstream repository.
- Can be used as an interactive boundary-refinement step with human review.

## MLCW recommendation

For stylized Thiri artwork, do not assume the fashion parser is accurate. Run a small benchmark first:
- Manually annotate ground-truth masks for face, hair, jewelry, top, longyi/skirt and drape on one canonical source.
- Compare parser class masks to manual masks using IoU and boundary F-score.
- If parser misses or confuses cartoon regions, use manual prompts + SAM 2.1 refinement.
- Keep the original pixels for protected identity regions; only composite within approved outfit masks.
- Store source SHA-256, dimensions, model/checkpoint version, prompts, raw masks, corrected masks, output image, QA JSON and reviewer decision.

## Existing QA harness

The synthetic pixel QA GitHub Actions run #2 passed 5/5 tests. This validates the QA harness behavior only; it is not a Thiri image benchmark.

## Run #32 acceptance gate

Do not claim actual visual QA PASS until:
1. Full-resolution Thiri base and P01 source/layers are available.
2. Human-reviewed target and protected masks are saved.
3. Actual composite is generated.
4. Pixel QA report shows zero uncovered target pixels, zero protected-region changes and zero spillover (or approved tolerance with explicit reviewer decision).
5. Reviewer signs off on visual likeness and garment alignment.

Status: research/design complete; real-image benchmark blocked on source assets.
