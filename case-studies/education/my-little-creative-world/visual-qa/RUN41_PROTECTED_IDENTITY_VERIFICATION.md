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
