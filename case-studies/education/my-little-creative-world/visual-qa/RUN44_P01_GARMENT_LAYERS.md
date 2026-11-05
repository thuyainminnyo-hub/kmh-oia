# MLCW V1.0.8 — Run #44 P01 Garment Sublayer Segmentation

**Date:** 2026-11-01  
**Status:** Three diagnostic candidate layers generated; final segmentation and P01 composite HOLD.

## Source
- `15312(1).png`
- Dimensions: 225×431 RGBA.
- SHA-256: `c241aa5c9e1a65b58f4b317c291bf7dfd92be9cedf4d62b35f7874ece6193517`.

## Segmentation method
HSV color thresholds constrained by hand-authored spatial polygons/regions. The three masks are independent and may overlap, especially the sheer drape. This is a candidate segmentation method, not manual pixel tracing or semantic-model certification.

## Actual layer measurements
- Gold Blouse: 15,723 candidate pixels; bbox [0,34,167,166].
- Ruby Longyi: 31,765 candidate pixels; bbox [0,142,136,431].
- Cream/Gold Drape: 15,179 candidate pixels; bbox [93,58,184,357].

Overlap counts:
- Blouse ∩ Longyi: 525 pixels.
- Blouse ∩ Drape: 5,852 pixels.
- Longyi ∩ Drape: 1,398 pixels.

## Findings
- The source garment is clipped at the left and bottom canvas edges.
- Drape transparency/overlap means the drape mask is intentionally independent and can overlap blouse and longyi.
- Some garment color regions may be missed by fixed HSV thresholds.
- Attachment tabs, dark outlines and cut-edge cleanup remain.
- No missing garment geometry has been invented or filled.

## Evidence in Library
All candidate RGBA layers, masks, white/dark/magenta previews, contact sheet and JSON metrics saved under `/My Little Creative World/Run 44/`.

## Reusable code
- `p01_layer_segmentation.py`
- `test_p01_layer_segmentation.py`
Local unit tests: **3 passed, 0 failed**.

## Gate
- Three layer candidates generated: PASS (diagnostic only).
- Independent masks/overlap recorded: PASS.
- Final blouse edge: HOLD.
- Final longyi edge: HOLD.
- Final drape transparency/edge: HOLD.
- Attachment tab removal: NOT COMPLETE.
- Missing clipped source geometry: NOT RECOVERABLE from this file.
- Thiri v5 alignment: NOT RUN.
- P01 character composite: NOT RUN.

## Autodesk Maya documentation applied to workflow design
- UV Editor RGB/RGBA/Alpha and Unfiltered view: https://help.autodesk.com/view/MAYAUL/2027/ENU/?guid=GUID-C697ECFC-64F2-4F1E-9A2C-EF1DCF9CE163
- Create PSD layer sets from Maya: https://help.autodesk.com/view/MAYAUL/2027/ENU/?guid=GUID-B750BF4E-2343-4AA0-A09F-C7FA5F270B95
- Use PSD networks as textures: https://help.autodesk.com/view/MAYAUL/2027/ENU/?guid=GUID-A7687378-DC86-4B80-A208-80AC151BFE54

**Run #44 decision:** segmentation candidate package ready for review; do not use as final outfit layers until edges, overlaps and clipped source boundaries are repaired and verified.
