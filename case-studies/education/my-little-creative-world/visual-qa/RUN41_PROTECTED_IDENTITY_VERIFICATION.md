# MLCW V1.0.8 — Run #41 Protected Identity Regression Verification

**Date:** 2026-11-01  
**Input:** Original Thiri source, Run #40 composite, protected-head mask.

## Actual image execution

The protected-head identity regression tool compared RGB values from the canonical source against the Run #40 composite within the protected mask.

- Canvas: 1024×1536.
- Protected mask pixels: 82,611.
- Fully opaque protected core: 81,164 pixels.
- Exact RGB matches in core: 81,164 / 81,164.
- Changed RGB pixels in opaque core: 0.
- Exact match ratio in opaque core: 100%.
- Changed RGB pixels across entire feathered mask: 88 (boundary blend only).
- Maximum RGB channel delta in opaque core: 0.

**Interpretation:** the original source RGB values are preserved exactly in all fully opaque pixels of the defined head core. The 88 differences fall within the feathered mask boundary, where alpha compositing blends source and reconstructed content. This is not a whole-character identity score.

## Automated regression harness

Added:
- `identity_preservation.py` — verifies source/output dimensions, protected mask dimensions, nonempty mask and exact RGB equality on fully opaque core.
- `test_identity_preservation.py` — four unit tests:
  1. Identical protected core returns PASS.
  2. A changed protected pixel returns FAIL.
  3. Mask dimension mismatch fails closed.
  4. Empty mask fails closed.

Local test result: **4 passed, 0 failed**.

## Output
- Prototype: `MLCW_Run40_Original_Head_Preserved_Body_Reconstruction_v4.png`
- Protected mask: `MLCW_Run40_Original_Head_Protected_Mask.png`
- Metrics: `MLCW_Run41_Protected_Identity_Verification.json`

## Gate

- Run #40 head-core exact pixel regression: PASS.
- Run #41 regression tool unit tests: local PASS (4/4).
- Remote GitHub Actions for the newly added tests: pending.
- Neck seam / mask boundary human review: pending.
- Full body proportion approval: pending.
- Master Base promotion: HOLD.
- P01 segmentation/composite: NOT RUN.

Do not overgeneralize the 100% core match to feathered boundary pixels, reconstructed body, or overall visual identity.


## Remote GitHub Actions evidence

- Workflow: MLCW Visual Pixel QA
- Run: #63
- Run ID: `41329342068`
- Conclusion: **SUCCESS**
- Python 3.12 unit tests: **13 passed, 0 failed**
- Included test groups:
  - Segmentation metrics: 4 tests
  - Protected identity regression: 4 tests
  - Pixel QA: 5 tests

Registry workflow:
- Workflow: MLCW Character Registry Validation
- Run: #83
- Run ID: `41329341947`
- Conclusion: **SUCCESS**
- JSON Schema, YAML schema/parity and retrieval tests completed successfully.

These CI runs validate the test harness and registry code. The actual Run #40 image verification was also run locally using the new `identity_preservation.py` tool and the real source/output/mask files; it reported 81,164/81,164 exact RGB matches in the fully opaque protected-head core. The CI unit tests themselves use synthetic images; they do not fetch or validate the actual Thiri images.

## Official research sources
- OpenAI edit API: https://developers.openai.com/api/reference/resources/images/methods/edit — transparent PNG/WebP output is supported for the current GPT Image 2.5 edit variants; masks are same-size PNGs, less than 4 MB, and are editable-region guidance.
- OpenAI image prompting: https://developers.openai.com/api/docs/guides/image-prompting — transparent output requires PNG/WebP and direct alpha inspection.
- Meta SAM 3.1 prompting: https://dev.meta.ai/docs/sam/segmenting — choose either a short concept phrase or box/point prompts, not both in one request; zero matches are a valid response.
- Meta SAM overview: https://dev.meta.ai/docs/sam/overview — masks supply geometry for measurement/cropping/compositing, not visual sign-off.

**Final Run #41 gate:** protected-head opaque core pixel preservation = PASS; automated regression CI = PASS; neck seam/body proportion human review = PENDING; Master Base approval = HOLD; P01 outfit compositing = NOT RUN.
