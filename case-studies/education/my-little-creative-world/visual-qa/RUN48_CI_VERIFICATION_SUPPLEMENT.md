# MLCW V1.0.8 — Run #48 CI Verification Supplement

**Date:** 2026-11-02

## GitHub Actions results
The component-refinement script, tests, report, metrics and component-decision register were committed to branch `feat/my-little-creative-world-prototype`.

For the latest component-decision commit `acb7575a73888c30d92561cb730a689eed4a7f33`, GitHub Actions returned:

- MLCW Visual Pixel QA #119 — run ID `41413224960`: **SUCCESS**. Decoded job log confirms **33 tests passed, 0 failed**, including all five `test_run48_refine` cases.
- MLCW Character Registry Validation #139 — run ID `41413225085`: **SUCCESS**.
- KMH OIA Tests #1531 — run ID `41413224994`: **SUCCESS**.
- KMH OIA Validation #1450 — run ID `41413224977`: all four jobs **SUCCESS**.

[MLCW Visual Pixel QA #119](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41413224960)

## CI scope boundary
The 33 unit tests include five synthetic tests for Run #48 component assignment rules. They confirm expected code behavior on synthetic inputs (shoulder assignment, tab/shoulder split, sleeve-to-drape split, dimension validation and fail-closed handling of a small ambiguous component). They do not certify pixel-perfect garment contours in the original illustration or true sheer-fabric alpha.

## Evidence-based Run #48 metrics
- Source alpha foreground: 464,840 pixels.
- Run #47 assigned: 432,161 pixels (92.970%).
- Run #48 assigned: 463,310 pixels (99.671%).
- Newly assigned from Run #47 residual: 31,149 pixels (95.318% of prior residual).
- Paper-tab candidate pixels withheld: 1,457.
- Ambiguous pixels kept unassigned: 73.
- Pairwise overlap between the three refined layer masks: zero pixels.

## Official technical references reviewed
- Meta SAM 3.1 accepts concept phrases or spatial prompts using boxes and positive/negative points; use it as a proposed mask-generation/refinement route, not as a substitute for human QA: https://dev.meta.ai/docs/sam/segmenting
- Adobe Photoshop's selection/mask refinement offers On Black, On White and Black-and-White mask views plus Color Aware and Object Aware modes: https://helpx.adobe.com/photoshop/desktop/make-selections/refine-modify-selections/refine-your-selection-and-mask.html
- Current research on transparent-object matting: https://doi.org/10.1145/3785468

SAM 3.1 inference and Photoshop editing were researched but **not executed** in Run #48. The actual refinement used OpenCV connected components, visual inspection of residual component crops, and manually authored assignment/split rules.

## Production gate
P01 remains a diagnostic candidate. Human contour sign-off, true drape transmission alpha, hidden garment regions under the drape, Thiri v5 alignment and final protected-identity composite QA remain pending. Do not mark the character production-ready or merge/launch on this evidence alone.
