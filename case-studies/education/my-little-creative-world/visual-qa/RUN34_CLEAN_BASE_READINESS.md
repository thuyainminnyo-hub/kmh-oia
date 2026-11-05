# MLCW V1.0.8 — Run #34 Clean Master Base Readiness & P01 Reconstruction Gate

**Date:** 2026-11-01  
**Decision:** HOLD — do not composite P01 onto the current Thiri reference.

## 1. Source files inspected

| Asset | Dimensions | Mode | Alpha | Assessment |
|---|---:|---|---|---|
| `15309(1).png` — Thiri | 1024×1536 | RGBA | min=max=255 (fully opaque) | Canonical identity reference only; cream blouse and longyi cover the body. Not a clean body base. |
| `15312(1).png` — P01 | 225×431 | RGBA | 36.346% transparent | Outfit concept panel, not fitted garment layers. |
| `MLCW_Run33_P01_Main_Component_Cutout_Candidate.png` | 225×431 | RGBA | candidate cutout | Still contains an adjacent purple fragment and edge/crop artifacts; diagnostic only. |

## 2. Findings

- Thiri's source has no transparent pixels. The existing cream blouse and longyi are baked into the RGB image; removing them cannot reveal the covered body underneath.
- P01's largest alpha component contains 59,523 pixels (96.428% of opaque pixels), bounding box `[0,18,189,431]`, touching the left and bottom panel edges.
- P01 has 75 connected alpha components. The second-largest component has 1,875 pixels at `[194,85,225,205]` and is the neighboring purple design fragment.
- P01's main component is clipped at the panel boundary; the current cutout candidate is not a complete, production-ready garment layer.
- No clean blouse, longyi, shawl layers or garment-to-body anchor coordinates are available in the supplied sources.

## 3. Run #34 execution result

| Gate | Result | Reason |
|---|---|---|
| Source-file inspection | PASS | Original source files read locally; dimensions/modes/alpha checked. |
| Clean Thiri body base | BLOCKED | Existing reference is fully opaque and clothed. |
| P01 clean extraction | PARTIAL | Main component candidate exists, but adjacent fragment and clipping remain. |
| P01 garment segmentation into layers | NOT RUN | Concept panel is not cleanly separated into blouse/longyi/shawl. |
| Garment alignment / anchors | NOT RUN | No approved body base or fit coordinates. |
| Actual composite | NOT RUN | Would require inventing hidden body pixels and garment geometry. |
| Protected-region pixel QA | NOT RUN | No valid composite or approved masks to compare. |

## 4. Required input to unlock the next gate

Preferred:
1. A clean Thiri base with the same face, hair, body pose and proportions, but with a neutral underlayer/body base and no cream outer outfit; transparent background preferred.
2. P01 as separate, uncropped transparent layers: blouse, longyi and shawl/drape. Include full hems, sleeve edges and any overlap pieces.
3. If a clean base cannot be supplied, explicit approval is required for a reconstruction workflow. Reconstruction must be labelled generated/reconstructed, not original source pixels, and face/hair identity must be independently reviewed.

## 5. Acceptance criteria for the next execution

- Source dimensions and SHA-256 hashes recorded.
- Human-approved masks for face, hair, skin, hands, earrings/accessories and outfit regions.
- P01 garment layers have no adjacent-color fragments and no clipped boundaries.
- Anchor points for neck, shoulders, waist, hip and hem are recorded.
- Composite is rendered only after the above inputs are approved.
- Pixel QA reports target coverage, uncovered pixels, spillover, and protected-region changed pixels on aligned source/output images.
- Human review signs off before any PASS or production promotion.

**Run #34 conclusion:** asset readiness was assessed with real local source files. Clean-base readiness is BLOCKED; P01 reconstruction readiness is PARTIAL. No real outfit application or visual identity preservation is claimed. Keep Character Registry lifecycle at `QA Pending`, Master Lock at `Source Partial`, and visual QA at `Pending`.
