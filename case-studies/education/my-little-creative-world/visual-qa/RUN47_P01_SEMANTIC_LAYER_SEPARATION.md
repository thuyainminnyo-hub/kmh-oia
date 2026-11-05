# MLCW V1.0.8 — Run #47: P01 Semantic Layer Separation (Diagnostic)

**Date:** 2026-11-02  
**Decision:** Three visible-region mask candidates generated; final semantic layers remain **HOLD**.

## Source and method
- Input: Run #46 `P01_Outfit03_Transparent_Candidate_v2.png`, 617×1148 RGBA.
- Source lineage: recovered project PDF, page 3, Outfit 03 “Gold & maroon”.
- Method: manually authored polygon regions for Gold Blouse, Ruby Longyi and Cream/Gold Drape, intersected with Run #46 alpha. Masks are partitioned to prevent overlap in this visible-region split.
- No SAM 3.1 / SAM 2 inference or OpenCV GrabCut operation was run; these were researched only.
- No hidden clothing regions were reconstructed.

## Candidate layer metrics
| Layer | Mask pixels | Partial-alpha pixels | Bounding box (xyxy) |
|---|---:|---:|---|
| Gold Blouse | 107,079 | 684 | [4, 40, 582, 503] |
| Ruby Longyi | 231,353 | 1,208 | [106, 355, 443, 1142] |
| Cream/Gold Drape | 93,729 | 146 | [363, 78, 613, 930] |

## Source foreground coverage
- Source alpha foreground pixels (`alpha > 16`): 464,840
- Pixels assigned to one of the three masks: 432,161
- Unassigned source foreground pixels: 32,679
- Diagnostic coverage: **92.970%**
- Pairwise mask overlap: 0 pixels (by construction)

The magenta overlay highlights all source foreground pixels not assigned to a layer. This includes paper tabs and unreviewed garment-edge/overlap areas; it must not be treated as a pure “tab-only” count.

## Visual QA result
The contact sheet confirms that three separate cutout candidates were produced. The overlay still shows material unassigned regions around the right-side sleeve/drape boundary and some outer contours. The first-pass polygons therefore require manual refinement before these layers are used for character fitting.

## Important alpha limitation
The drape source is a flattened RGB render on a white page. The available alpha is inherited from the Run #46 outer-silhouette candidate and does **not** represent the original fabric's true translucency. A production-quality sheer shawl matte requires an original layered/transparent source or an approved reconstruction/matting pass. Hidden blouse/longyi pixels beneath the drape are also unavailable in the flattened source.

## Local automated tests
- Four tests passed, zero failed.
- Tests cover output keys and dimensions, boolean mask format, non-overlap partition, wrong input dimensions and empty-alpha behavior.
- These are code/helper tests, not certification of visual boundary accuracy.

## Evidence artifacts
Saved under `/My Little Creative World/Run 47/`: three candidate PNGs, three masks, white/dark/magenta previews, contact sheet, unassigned-pixel overlay, visible-layer stack preview, metrics JSON, script and tests.

## Gate
| Check | Status |
|---|---|
| Three visible-region masks generated | PASS — diagnostic |
| Local code tests | PASS — 4/4 |
| Pairwise mask overlap | PASS — 0 pixels |
| Source foreground coverage | 92.970% — incomplete |
| Manual boundary acceptance | PENDING |
| Paper-tab cleanup | PENDING |
| True drape alpha | NOT RECOVERED |
| Hidden garment reconstruction | NOT RUN |
| Thiri v5 alignment | NOT RUN |
| P01 composite / protected-identity QA | NOT RUN |

**Run #47 decision:** Keep all three candidates diagnostic. Do not mark outfit assets production-ready or promote the Thiri Character Registry. Continue with targeted edge refinement and an approved source/matte for the drape.

## Official research references
- Meta SAM 3.1 prompt segmentation: https://dev.meta.ai/docs/sam/segmenting
- Meta SAM overview: https://dev.meta.ai/docs/sam/overview
- Meta SAM 3 research page: https://ai.meta.com/research/sam3
- Adobe Photoshop layer masks: https://helpx.adobe.com/photoshop/desktop/create-masks/layer-masks/add-layer-masks.html

SAM 3.1 and Photoshop layer-mask workflows are potential follow-up methods; they were not executed in Run #47.


## GitHub Actions CI — dependency failure and successful rerun

The first pull-request CI attempt after Run #47 files were added was **MLCW Visual Pixel QA #103**, run ID `41384049174`, conclusion **FAILURE**. The job installed NumPy and Pillow but failed to import three P01 test modules because `cv2` was not installed. The error was `ModuleNotFoundError: No module named 'cv2'`; 20 tests were discovered and three module-import errors occurred.

**Root cause corrected:** added pinned `opencv-python-headless==5.0.0.93` to `visual-qa/requirements.txt`. PyPI lists the 5.0.0.93 release and ABI3 wheels for current Python interpreters. See [PyPI package record](https://pypi.org/project/opencv-python-headless/).

**Successful rerun evidence for commit `4dd0bf4a90467f496015e5c410b316d67b8113a6`:**

- MLCW Visual Pixel QA #105 — run ID `41384204559`: **SUCCESS**; OpenCV installed; **28 tests passed, 0 failed**.
- MLCW Character Registry Validation #125 — run ID `41384204525`: **SUCCESS**.
- KMH OIA Tests #1490 — run ID `41384204578`: **SUCCESS**.
- KMH OIA Validation #1409 — run ID `41384204509`: **SUCCESS**.

[View MLCW Visual Pixel QA #105](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41384204559)

**CI scope note:** these are code/test-suite checks. The four Run #47 semantic-mask tests use synthetic inputs and verify mask dimensions, output types, non-overlap, rejection of invalid dimensions and empty-alpha behavior. They do not independently certify that the real P01 masks follow the exact garment contours. The measured 92.97% foreground assignment and image previews are separate local artifact inspections.

The PR #175 remains open; no merge or production release is claimed.
