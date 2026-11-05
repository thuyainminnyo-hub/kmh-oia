# MLCW V1.0.8 — Run #46: P01 Master-Sheet Extraction Candidate

**Date:** 2026-11-02  
**Decision:** Extraction candidate generated; Production Gate remains **HOLD**.

## Recovered source
- Source PDF: `My_Little_Creative_World_Myanmar_Prototype_v1.pdf`
- Page 3: `02 · Outfit Asset Sheet`
- Target: working Outfit 03, `Gold & maroon`, visually matching P01 (`15312(3).png`).
- 400 DPI page render: 4678 × 3308 px.
- Safe crop coordinates: [1840,470,2640,1730], 800 × 1260 px.

## Execution
- OpenCV HSV foreground discrimination and connected-component selection against the near-white paper.
- Five manually defined tab-exclusion regions; chromatic garment pixels restored in those regions to reduce accidental garment loss.
- Only small enclosed mask holes up to 90 pixels filled.
- Transparent RGBA silhouette candidate exported with a narrow antialias estimate.
- No missing garment geometry invented or reconstructed.

## Output
- Dimensions: **617 × 1148 px RGBA**
- Foreground mask: 464,840 pixels
- Fully opaque alpha: 460,101 pixels
- Partial alpha: 4,739 pixels
- Transparent pixels within output canvas: 243,476
- Bounding box: [93,41,710,1189] on the safe crop.

## Limitations
- Preview shows remaining paper-tab/edge remnants near the upper-right shoulder and a few edge irregularities. Manual edge cleanup remains required.
- Source is a flattened RGB PDF render against white, not an original layered PSD/transparent source.
- Shawl translucency is flattened against white. Candidate alpha represents outer silhouette and antialias edge only; it does not recover true sheer-fabric alpha.
- No final blouse/longyi/drape sublayer segmentation, Thiri v5 fitting, final composite, protected-region comparison, or identity regression QA was performed.
- SAM 2 was researched but not run in this environment.

## Automated tests
Local tests: **4 passed, 0 failed**. They test helper behavior, not visual garment edge correctness.

## Evidence gate
| Check | Status |
|---|---|
| High-resolution Outfit 03 source | PASS |
| Candidate RGBA silhouette | PASS |
| Alpha and mask metrics recorded | PASS |
| Unit tests | PASS — 4/4 |
| All tabs/edge artifacts removed | HOLD |
| True drape alpha recovered | NOT AVAILABLE FROM FLATTENED SOURCE |
| Garment sublayer separation | NOT RUN |
| Thiri v5 alignment | NOT RUN |
| Final P01 composite / identity QA | NOT RUN |

## Web research
- Meta SAM 2: promptable segmentation for objects in images/video using clicks, boxes or masks. https://ai.meta.com/research/sam2/
- OpenCV GrabCut: mask-based or rectangle-initialized foreground extraction with iterative refinement. https://docs.opencv.org/4.9.0/d3/d47/group__imgproc__segmentation.html
- Pillow PNG docs: RGBA PNG image support and transparency handling. https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html

**Outcome:** reproducible diagnostic silhouette candidate exists. It is not approved as a production outfit layer. Manual edge, tab, shawl-alpha, sublayer and fit review remain blocking gates.
