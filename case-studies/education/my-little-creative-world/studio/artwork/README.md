# MLCW Thiri artwork source workflow

This is the source-of-truth asset specification for the 2D paper-doll pilot. It is a production plan, not a claim that the editable PSD or separated garment layers have already been created.

## SketchBook setup

1. Create a 450 × 450 canvas. Keep the source coordinate system fixed throughout the artwork workflow.
2. In SketchBook Pro Desktop, enable **Add Image: import into a new layer**, then use **File → Add Image** to import `assets/thiri-base.jpg`.
3. Rename that image layer `REFERENCE_ORIGINAL_LOCKED`. Confirm the full 450 × 450 image is present, then lock the layer. Do not crop, rotate, stretch, paint on, or overwrite it.
4. Create `BODY_BASE_RECONSTRUCTION` on a separate layer. Carefully rebuild the character base so the original purple clothing is not visible beneath future garments. Preserve the face, hair, hair ornament, skin, pose, and proportions. Do not infer hidden anatomy; use conservative garment coverage.
5. Create ten groups named `OUTFIT_001` through `OUTFIT_010`. Each group must contain `BLOUSE`, `SASH`, `HTAMEIN`, and `DETAILS` layers. Keep all garments aligned to the same 450 × 450 source canvas.
6. Put temporary shoulder, neckline, waist, and hem guides in `QA_OVERLAY_GUIDES`. Hide this group before export.

SketchBook layer availability depends on device capability. If the mobile device cannot comfortably hold the full layer stack, work on one outfit group per file and combine at desktop; do not flatten the editable master prematurely.

## Export rules

- Save the editable master as PSD so the layers remain editable.
- For separate garment PNGs, hide the Background layer to create transparency, then export PNG. PNG is a flattened delivery format; retain the PSD as the master.
- The web app preview is 1024 × 1536. Fit the square character into the portrait canvas using contain scaling and center it. Never stretch the 450 × 450 source.
- Keep the original JPEG unchanged. The expected SHA-256, Git blob SHA-1, byte count and dimensions are recorded in `layer-manifest.json`.

## Before a garment enters the app

Run the asset-integrity test, inspect transparency, view at 100%, check shoulder/neckline/waist/hem alignment, confirm there is no old purple clothing showing through, and run desktop/mobile Playwright tests. The original asset test is intentionally a hard gate and currently reports the repository mismatch until the exact original bytes are committed.

## Autodesk references

- [Adding an image](https://help.autodesk.com/view/SKETPRO/ENU/?guid=SKETPRO_Help_sb_tools_how_to_add_image_html)
- [Layer Editor](https://help.autodesk.com/view/SKETPRO/ENU/?guid=SKETPRO_Help_sb_layers_layer_editor_html)
- [Layers in SketchBook Pro](https://help.autodesk.com/view/SKETPRO/ENU/?guid=SKETPRO_Help_sb_layers_html)
- [Creating an alpha channel](https://help.autodesk.com/view/SKETPRO/ENU/?guid=SKETPRO_Help_sb_layers_layer_editor_create_alpha_channel_html)
- [File Saving in SketchBook Pro](https://help.autodesk.com/view/SKETPRO/ENU/?guid=SKETPRO_Help_sb_file_saving_html)


## V1.0.8 in-app neutral base implementation

The Studio renders an opaque neutral base SVG over the locked original JPEG in every state, including reset. The base consists of `BODY_BASE_TOP`, `BODY_BASE_LOWER`, and `BASE_NECKLACE` groups. A browser pixel test composites the original JPEG and base SVG, then checks a known lower-htamein source pixel is covered by the neutral base color. The original JPEG itself remains unchanged and continues to pass its source SHA/Git blob integrity gate.

Each selected outfit renders separate addressable `BLOUSE`, `SASH`, `HTAMEIN`, and `DETAILS` SVG groups above the neutral base. These remain interactive concept overlays; they are not yet final hand-authored cultural clothing artwork or a layered PSD master. Human review and detailed asset production remain required.
