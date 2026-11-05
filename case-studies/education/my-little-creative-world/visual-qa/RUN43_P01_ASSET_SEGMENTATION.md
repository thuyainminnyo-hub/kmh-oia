# MLCW V1.0.8 — Run #43 P01 Gold & Ruby Asset Segmentation

**Date:** 2026-11-01  
**Decision:** SOURCE INTAKE PASS / MAIN COMPONENT DIAGNOSTIC CUTOUT / FINAL GARMENT LAYER HOLD.

## Run #42 approval
The user approved Run #42 v5 visually ("အိုကေအဆင်ပြေတယ်"). Record this as **user visual review accepted** for the v5 reconstruction working base. Do not interpret it as full body-proportion certification or final product release.

## Source asset
- File: `15312(1).png`
- Working slot: P01
- Design: gold blouse, ruby/red patterned longyi, cream/gold drape.
- Dimensions: 225×431 RGBA.
- SHA-256: `c241aa5c9e1a65b58f4b317c291bf7dfd92be9cedf4d62b35f7874ece6193517`.
- Transparent pixels: 35,247 (36.346%).
- Partial alpha pixels: 513.
- Opaque pixels: 61,215.
- Connected components: 75.

## Actual connected-component processing
- Largest component: 59,523 pixels (96.428% of nontransparent pixels).
- Largest component bbox: `[0,18,189,431]`.
- Second-largest component: 1,875 pixels; bbox `[194,85,225,205]`; corresponds to adjacent purple outfit fragment.
- Largest component was isolated into a diagnostic RGBA cutout; the separate purple component is excluded.

## Visual inspection findings
The diagnostic cutout still contains visible black attachment tabs/connector marks at the top and right edges. The largest component also touches the left and bottom source-panel boundaries, so parts of the garment may be clipped. No missing pixels have been invented or reconstructed.

## Evidence artifacts saved in Library
- `/My Little Creative World/Run 43/P01_Main_Component_Cutout_Candidate.png`
- `/My Little Creative World/Run 43/P01_Main_Component_Mask.png`
- `/My Little Creative World/Run 43/P01_Main_Component_White_Preview.jpg`
- `/My Little Creative World/Run 43/P01_Main_Component_Dark_Preview.jpg`
- `/My Little Creative World/Run 43/P01_Main_Component_Magenta_Preview.jpg`
- `/My Little Creative World/Run 43/P01_Segmentation_Contact_Sheet.jpg`
- `/My Little Creative World/Run 43/P01_Segmentation_Metrics.json`

## Reusable segmentation utility
Added `p01_component_extract.py`. It extracts the largest alpha-connected component but explicitly warns that attached tabs may remain and edge-touch may indicate clipping. It does not claim final garment readiness.

## Gate status
- P01 source intake: PASS.
- Adjacent purple fragment isolation: PASS (separate component excluded).
- Attachment tab cleanup: PENDING.
- Garment boundary repair: PENDING; requires uncropped source or user-approved reconstruction.
- Blouse / longyi / drape sublayer segmentation: NOT RUN.
- Fit/alignment to Thiri v5: NOT RUN.
- P01 composite: NOT RUN.
- Master working base: Run #42 v5 visually accepted by user; keep provisional until proportions/technical gates completed.

## Official research references
- OpenAI Image Edit API: https://developers.openai.com/api/reference/resources/images/methods/edit — transparent background options and mask/markup editing.
- OpenAI Image Prompting: https://developers.openai.com/api/docs/guides/image-prompting — inspect decoded alpha; checkerboard is not transparency.
- Meta SAM segmentation: https://dev.meta.ai/docs/sam/segmenting — localized prompts for object segmentation; masks still need review.

**Run #43 result:** P01 diagnostic extraction completed. Final garment layer is not ready for character compositing.


## GitHub Actions verification

- MLCW Visual Pixel QA run #76 (ID `41330247447`): **SUCCESS**.
- MLCW Character Registry Validation run #96 (ID `41330247485`): **SUCCESS**.
- KMH OIA Tests run #1433 (ID `41330247570`): **SUCCESS**.
- KMH OIA Validation run #1352 was still in progress when checked.

These CI workflows validate the existing code/test suites and registry. They do not certify P01 as a production-ready garment or verify the actual character fit.
