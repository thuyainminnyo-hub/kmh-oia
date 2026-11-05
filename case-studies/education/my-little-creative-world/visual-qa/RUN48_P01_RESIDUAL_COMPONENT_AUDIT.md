# My Little Creative World V1.0.8 — Run #48
## P01 Residual Component Audit & Boundary Refinement

**Date:** 2026-11-02  
**Status:** Refined diagnostic garment masks generated; production gate remains **HOLD**.

## Objective
Audit the 32,679 source-foreground pixels left unassigned by Run #47, distinguish garment-edge fragments from paper attachment tabs, and return only visually supportable pixels to the relevant layer. Ambiguous pixels remain unassigned.

## Source and reproducibility
- Source: Run #46 `P01_Outfit03_Transparent_Candidate_v2.png`
- Canvas: 617 × 1148 RGBA
- Existing masks: Run #47 Gold Blouse, Ruby Longyi and Cream/Gold Drape masks
- Actual method: OpenCV 8-connected component analysis, full-resolution visual component-crop inspection, manually specified component-to-layer rules, and a polygon split for the connected top-right paper tab / blouse shoulder edge.
- SAM 3.1 and Photoshop refinement were researched, **not executed** in this run.

## Residual audit result
Run #47 had 32,679 source alpha-foreground pixels not assigned to any of the three garment masks.

Run #48 inspected the residual as 29 connected components. Major visible components were classified as follows:

- Gold Blouse shoulder / sleeve / cuff contour: 7,527 pixels before the top-right shoulder/tab split was refined; total added to the blouse after that split: **8,626 px**.
- Ruby Longyi bottom hem: **414 px**.
- Cream/Gold Drape right edge, lower trailing panel and tip: **22,109 px**.
- Connected top-right attachment tab component: split into **1,099 px** of blouse shoulder contour and **1,316 px** of tab candidate.
- Left-side attachment tab candidates: **141 px** withheld.
- Other unresolved small component(s): **73 px** kept unassigned.

Total newly assigned to garment masks: **31,149 px**, or **95.318%** of Run #47's previously unassigned foreground.

## Final mask metrics
- Source alpha foreground (`alpha > 16`): **464,840 px**
- Run #47 assigned: 432,161 px
- Run #48 assigned: **463,310 px**
- Run #48 garment-mask coverage: **99.671%**
- Pairwise overlap between the three refined masks: **0 px**
- Pixels withheld as paper-tab candidates: **1,457 px**
- Residual pixels still ambiguous: **73 px**

### Per-layer results
| Layer | Run #47 mask | Run #48 mask | Added pixels |
|---|---:|---:|---:|
| Gold Blouse | 107,079 | **115,705** | 8,626 |
| Ruby Longyi | 231,353 | **231,767** | 414 |
| Cream/Gold Drape | 93,729 | **115,838** | 22,109 |

These figures measure the pixel areas of the diagnostic masks. They are not a human sign-off of contour quality, garment fit, or final product coverage.

## Visual QA findings
- The left shoulder and left sleeve outer contours were missing from the earlier polygons and are now restored as candidate blouse pixels.
- The right outer contour was a connected component crossing the sleeve-cuff / shawl boundary. It was split at y=505: upper part to blouse, lower part to drape.
- The large lower trailing panel and lower tip were restored to the drape candidate.
- The bottom hem edge was restored to the longyi candidate.
- The top-right paper tab was not removed as one whole connected component; its polygon was split from the adjacent blouse shoulder edge to avoid deleting garment pixels.
- The left-side paper tab candidate was excluded. Tiny ambiguous components remain withheld.

The green overlay indicates pixels recovered into garment masks; magenta indicates pixels withheld as tabs or still ambiguous. See `RUN48_P01_Component_Audit_Contact_Sheet.jpg` and `RUN48_P01_Residual_Classification_Overlay.jpg`.

## Alpha / transparency limitation
The source remains a flattened RGB PDF-derived illustration with an estimated outer-silhouette alpha. The drape's original transmission alpha is not present in this source, so the new drape candidate preserves the available silhouette alpha but does **not** claim true sheer-fabric transparency.

This limitation aligns with current matting research: a 2026 ACM paper discusses that alpha estimation for transparent objects is materially harder than opaque-object segmentation and separates foreground segmentation from transparency prediction. Official research: https://doi.org/10.1145/3785468.

## Web research applied to the next workflow
- Meta SAM 3.1 supports concept prompts or box / positive-point / negative-point prompts and returns object masks: https://dev.meta.ai/docs/sam/segmenting
- Adobe Photoshop selection refinement documents Color Aware and Object Aware refine modes and preview modes such as On Black, On White, Overlay and Black and White: https://helpx.adobe.com/photoshop/desktop/make-selections/refine-modify-selections/refine-your-selection-and-mask.html
- These are candidate next-step tools. Neither SAM 3.1 inference nor Photoshop was run in Run #48.

## Automated tests
Local Run #48 unit tests: **5 passed, 0 failed**. Tests cover left-shoulder attribution, tab/shoulder splitting, sleeve-to-drape split, input dimension validation and fail-closed behavior for a tiny uncertain component. They use synthetic masks and do not constitute real-image contour certification.

## Evidence artifacts
Saved under `/My Little Creative World/Run 48/`:
- `P01_Gold_Blouse_Refined_v2.png` + mask
- `P01_Ruby_Longyi_Refined_v2.png` + mask
- `P01_Cream_Gold_Drape_Refined_v2.png` + mask
- White / dark / magenta previews for each refined layer
- `RUN48_P01_Refined_Layer_Contact_Sheet.jpg`
- `RUN48_P01_Visible_Layer_Stack_Preview.jpg`
- `RUN48_P01_Residual_Classification_Overlay.jpg`
- `RUN48_P01_Component_Audit_Contact_Sheet.jpg`
- `RUN48_P01_Unassigned_Residual_Mask.png`
- `RUN48_P01_Excluded_Paper_Tab_Candidate_Mask.png`
- `RUN48_P01_Component_Decisions.json`
- `RUN48_P01_REFINEMENT_METRICS.json`
- `run48_refine.py`, `test_run48_refine.py`

## Gate
| Gate | Status |
|---|---|
| Residual component visual audit | PASS — diagnostic |
| Major shoulder / sleeve / drape / hem components assigned | PASS — diagnostic |
| Three masks pairwise non-overlapping | PASS — 0 px |
| Source foreground assigned to garment masks | 99.671% |
| Paper-tab candidate pixels withheld | 1,457 px |
| Ambiguous residual pixels | 73 px — HOLD |
| Local helper tests | PASS — 5/5 |
| Founder / human contour approval | PENDING |
| True sheer drape alpha | NOT RECOVERED |
| Hidden garment pixels beneath drape | NOT AVAILABLE |
| Thiri v5 alignment | NOT RUN |
| Final P01 composite / protected-identity QA | NOT RUN |

**Decision:** Run #48 materially reduces the residual mask gap and produces improved three-layer candidates, but the outputs remain diagnostic. Keep the Thiri Registry at QA Pending / Master Lock Source Partial and do not promote P01 to production.

## Next step — Run #49
1. Human review of the refined contact sheet and the 73 residual pixels.
2. Obtain the original layered/transparent P01 file if available, or approve a dedicated drape-alpha reconstruction workflow.
3. Evaluate SAM 3.1 box + positive/negative point masks against these manually reviewed candidate masks, if API access and model inference are available.
4. Only after mask approval, align to Thiri v5 and run protected-region pixel regression before a final composite.