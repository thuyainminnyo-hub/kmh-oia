# Run #47 — GitHub Actions CI Verification Supplement

**Date:** 2026-11-02

## Failure and fix
- Initial MLCW Visual Pixel QA #103 (run ID `41384049174`) failed because `cv2` was imported by new P01 test modules but OpenCV was absent from `visual-qa/requirements.txt`.
- Added `opencv-python-headless==5.0.0.93` to the pinned requirements.

## Successful validation
For the dependency-fix commit `4dd0bf4a90467f496015e5c410b316d67b8113a6`:
- MLCW Visual Pixel QA #105, run ID `41384204559`: SUCCESS; 28 tests passed, 0 failed.
- MLCW Character Registry Validation #125, run ID `41384204525`: SUCCESS.
- KMH OIA Tests #1490, run ID `41384204578`: SUCCESS.
- KMH OIA Validation #1409, run ID `41384204509`: SUCCESS.

For the later Run #47 report/metrics commit `86a86abffa8e963a490471b8f04bf8c12ca117a3`:
- MLCW Visual Pixel QA #109, run ID `41384344640`: SUCCESS; log confirms 28 tests passed, 0 failed.
- MLCW Character Registry Validation #129, run ID `41384344625`: SUCCESS.
- KMH OIA Tests #1492, run ID `41384344784`: SUCCESS.
- KMH OIA Validation #1411, run ID `41384344618`: SUCCESS.

## Scope boundary
These CI tests run synthetic fixtures and code-level validation. They do not prove that the real P01 garment masks match every visual contour, recover true drape transmission alpha, fit Thiri v5, or pass a final P01 composite/identity review. P01 remains a production HOLD.

[MLCW Visual Pixel QA #109](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41384344640)
