#!/usr/bin/env python3
"""Run 48: component-audited refinement for P01 visible garment masks.

The procedure adds only connected source-foreground components whose locations
were manually inspected in the generated Run 47 residual-component sheet.
Paper tabs / uncertain specks are intentionally left unassigned.
"""
from pathlib import Path
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw

LAYER_NAMES = ("Gold_Blouse", "Ruby_Longyi", "Cream_Gold_Drape")


def load_masks(mask_paths):
    masks = {}
    for name, path in zip(LAYER_NAMES, mask_paths):
        masks[name] = np.asarray(Image.open(path).convert("L")) > 0
    shapes = {m.shape for m in masks.values()}
    if len(shapes) != 1:
        raise ValueError("Input layer masks must share dimensions")
    return masks


def classify_residual_components(rgba, masks):
    h, w = rgba.shape[:2]
    for m in masks.values():
        if m.shape != (h, w):
            raise ValueError("Source and masks have different dimensions")
    source_fg = rgba[:, :, 3] > 16
    union = np.logical_or.reduce(list(masks.values()))
    residual = source_fg & ~union
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(
        residual.astype(np.uint8), connectivity=8
    )

    refined = {name: mask.copy() for name, mask in masks.items()}
    decisions = []
    yy, xx = np.ogrid[:h, :w]

    for i in range(1, count):
        x, y, bw, bh, area = map(int, stats[i])
        x2, y2 = x + bw, y + bh
        component = labels == i
        target = None
        method = "unassigned_uncertain"
        extra = None

        # The high, right-hand rectangular outlined element is the paper tab,
        # not garment. Keep it out of all garment masks.
        if x >= 345 and y <= 8 and x2 >= 470 and y2 <= 115:
            # Split the rotated paper tab from the connected blouse shoulder
            # contour; excluding the entire component would shave off garment pixels.
            tab_poly = np.zeros((h, w), np.uint8)
            cv2.fillPoly(tab_poly, [np.asarray([(430,0),(485,18),(449,88),(411,72)], np.int32)], 1)
            tab_part = component & (tab_poly > 0)
            shoulder_part = component & ~(tab_poly > 0)
            refined["Gold_Blouse"] |= shoulder_part
            method = "split_top_right_paper_tab_from_blouse_shoulder_edge"
            extra = {"blouse_edge_pixels": int(shoulder_part.sum()),
                     "tab_pixels": int(tab_part.sum()),
                     "tab_polygon_xy": [[430,0],[485,18],[449,88],[411,72]]}

        # Thin pale rectangle at the left skirt edge is the paper attachment tab.
        elif x >= 100 and x2 <= 125 and y >= 485 and y2 <= 600:
            method = "excluded_left_side_paper_tab"

        # Small upper neckline/outer-edge fragment visually belongs to blouse.
        elif x >= 195 and x2 <= 235 and y <= 55 and y2 <= 60 and area <= 100:
            target, method = "Gold_Blouse", "manual_visual_neckline_edge"

        # Missing left shoulder contour/outer gold pixels.
        elif x >= 55 and x2 <= 215 and y >= 35 and y2 <= 280 and area >= 500:
            target, method = "Gold_Blouse", "manual_visual_left_shoulder_contour"

        # Left sleeve outer contour fragments.
        elif x >= 70 and x2 <= 170 and y >= 285 and y2 <= 525 and area >= 500:
            target, method = "Gold_Blouse", "manual_visual_left_sleeve_contour"
        elif x < 85 and y >= 400 and y2 <= 530 and area >= 400:
            target, method = "Gold_Blouse", "manual_visual_cuff_outer_contour"

        # Long narrow right outer edge straddles sleeve cuff and drape side.
        # Split at the visible cuff/drape transition; do not invent geometry.
        elif x >= 495 and x2 <= 617 and y >= 180 and y2 >= 700 and area >= 5000:
            blouse_part = component & (yy < 505)
            drape_part = component & (yy >= 505)
            refined["Gold_Blouse"] |= blouse_part
            refined["Cream_Gold_Drape"] |= drape_part
            method = "manual_visual_split_at_sleeve_cuff_transition"
            extra = {"blouse_pixels": int(blouse_part.sum()),
                     "drape_pixels": int(drape_part.sum()),
                     "split_y": 505}

        # Inner lower trailing panel of the translucent shawl.
        elif x >= 425 and y >= 625 and y2 >= 900 and area >= 5000:
            target, method = "Cream_Gold_Drape", "manual_visual_lower_drape_panel"

        # Lower-right shawl tip/edge.
        elif x >= 585 and y >= 885 and area >= 100:
            target, method = "Cream_Gold_Drape", "manual_visual_drape_tip"

        # Bottom horizontal hem contour belongs to the longyi.
        elif x >= 220 and x2 <= 345 and y >= h - 12 and area >= 150:
            target, method = "Ruby_Longyi", "manual_visual_longyi_bottom_hem"

        if target:
            refined[target] |= component

        decisions.append({
            "component_id": i, "area_pixels": area,
            "bbox_xyxy": [x, y, x2, y2],
            "centroid_xy": [round(float(centroids[i][0]), 2), round(float(centroids[i][1]), 2)],
            "assignment": target or ("split" if extra else "excluded_or_unresolved"),
            "method": method, "details": extra
        })

    return refined, decisions, residual, source_fg


def save_rgba_layer(rgb, source_alpha, mask, output_path):
    alpha = np.where(mask, source_alpha, 0).astype(np.uint8)
    out = np.dstack([rgb, alpha])
    Image.fromarray(out, "RGBA").save(output_path)
    Image.fromarray((mask * 255).astype(np.uint8), "L").save(
        Path(output_path).with_name(Path(output_path).stem + "_Mask.png")
    )
    return alpha


def composite_preview(rgb, alpha, bg):
    a = alpha.astype(np.float32)[:, :, None] / 255.0
    b = np.full_like(rgb, bg, dtype=np.float32)
    return np.clip(rgb.astype(np.float32) * a + b * (1.0 - a), 0, 255).astype(np.uint8)


def run(input_png, mask_paths, outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    rgba = np.asarray(Image.open(input_png).convert("RGBA"))
    rgb, source_alpha = rgba[:, :, :3], rgba[:, :, 3]
    masks = load_masks(mask_paths)
    refined, decisions, original_residual, source_fg = classify_residual_components(rgba, masks)

    # Check pairwise overlap. This implementation preserves the Run 47 disjoint
    # partition and assigns each accepted residual component to one layer only.
    names = list(refined)
    overlap = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            overlap[f"{names[i]}__{names[j]}"] = int((refined[names[i]] & refined[names[j]]).sum())

    union = np.logical_or.reduce(list(refined.values()))
    unassigned = source_fg & ~union
    source_pixels = int(source_fg.sum())
    assigned_pixels = int(union.sum())
    component_totals = {}
    for name in names:
        old = masks[name]
        new = refined[name]
        alpha = save_rgba_layer(rgb, source_alpha, new,
                                outdir / f"P01_{name}_Refined_v2.png")
        component_totals[name] = {
            "run47_mask_pixels": int(old.sum()),
            "run48_mask_pixels": int(new.sum()),
            "added_pixels": int((new & ~old).sum()),
            "partial_alpha_pixels": int(((alpha > 0) & (alpha < 255)).sum()),
            "bbox_xyxy": [int(np.where(new)[1].min()), int(np.where(new)[0].min()),
                          int(np.where(new)[1].max()+1), int(np.where(new)[0].max()+1)]
        }
        for label, bg in {"White": (255,255,255), "Dark": (35,35,45),
                          "Magenta": (235,0,180)}.items():
            Image.fromarray(composite_preview(rgb, alpha, bg)).save(
                outdir / f"P01_{name}_{label}_Preview_v2.jpg", quality=95
            )

    # Visual status map: existing Run47 mask pixels retain their layer color;
    # recovered components are brighter; unassigned/uncertain remains magenta.
    palette = {"Gold_Blouse": (240, 165, 10), "Ruby_Longyi": (185, 15, 55),
               "Cream_Gold_Drape": (25, 145, 210)}
    overlay = np.full_like(rgb, 255)
    for name in names:
        color = np.asarray(palette[name], np.float32)
        overlay[refined[name]] = (rgb[refined[name]].astype(np.float32)*0.55 + color*0.45).clip(0,255).astype(np.uint8)
    added_union = union & ~np.logical_or.reduce(list(masks.values()))
    overlay[added_union] = (rgb[added_union].astype(np.float32)*0.35 + np.array([0,230,100])*0.65).clip(0,255).astype(np.uint8)
    overlay[unassigned] = (rgb[unassigned].astype(np.float32)*0.25 + np.array([255,0,220])*0.75).clip(0,255).astype(np.uint8)
    Image.fromarray(overlay).save(outdir / "RUN48_P01_Residual_Classification_Overlay.jpg", quality=95)

    # Component register/JSON
    decisions_path = outdir / "RUN48_P01_Component_Decisions.json"
    decisions_path.write_text(json.dumps(decisions, indent=2), encoding="utf-8")

    # Contact sheet
    sheet = Image.new("RGB", (927, 630), (246,246,246)); draw = ImageDraw.Draw(sheet)
    for i, name in enumerate(names):
        a = np.where(refined[name], source_alpha, 0).astype(np.uint8)
        im = Image.fromarray(composite_preview(rgb, a, (255,255,255)))
        im = im.resize((309, 574), Image.Resampling.LANCZOS)
        sheet.paste(im, (i*309, 52)); draw.text((i*309+8, 15), name, fill=(20,20,30))
    sheet.save(outdir / "RUN48_P01_Refined_Layer_Contact_Sheet.jpg", quality=95)

    # Save summary metrics. Original residual vs assigned vs excluded/unresolved.
    assigned_by_layer = {k: int((refined[k] & original_residual).sum()) for k in names}
    excluded = [d for d in decisions if d["method"].startswith("excluded_")]
    split_tab_pixels = sum(int((d.get("details") or {}).get("tab_pixels", 0)) for d in decisions)
    split_assigned_pixels = sum(int((d.get("details") or {}).get("blouse_edge_pixels", 0)) for d in decisions)
    accepted = [d for d in decisions if d["assignment"] in names or d["assignment"] == "split" or d.get("details")]
    metrics = {
        "run": 48,
        "source": Path(input_png).name,
        "dimensions_px": [int(rgba.shape[1]), int(rgba.shape[0])],
        "source_foreground_pixels_alpha_gt_16": source_pixels,
        "run47_assigned_pixels": int(np.logical_or.reduce(list(masks.values())).sum()),
        "run47_unassigned_pixels": int(original_residual.sum()),
        "run48_assigned_pixels": assigned_pixels,
        "run48_unassigned_pixels": int(unassigned.sum()),
        "run48_coverage_percent": round(assigned_pixels / max(1, source_pixels) * 100, 3),
        "recovered_from_residual_by_layer": assigned_by_layer,
        "excluded_component_pixels": int(sum(d["area_pixels"] for d in excluded) + split_tab_pixels),
        "split_component_garment_pixels": int(split_assigned_pixels),
        "residual_pixels_after_masks_including_tab_exclusions": int(unassigned.sum()),
        "unresolved_component_pixels": int(unassigned.sum() - (sum(d["area_pixels"] for d in excluded) + split_tab_pixels)),
        "component_count": len(decisions),
        "accepted_component_count": len(accepted),
        "excluded_component_count": len(excluded),
        "pairwise_overlap_pixels": overlap,
        "layers": component_totals,
        "manual_review_rules": [
            "Assign left shoulder/sleeve contour components to Gold Blouse based on full-resolution crop review.",
            "Split the long right-edge component at y=505: upper sleeve contour to blouse, lower drape contour to shawl.",
            "Assign the large inner lower trailing-panel component and small lower tip to Drape.",
            "Assign the bottom hem strip to Ruby Longyi.",
            "Split the connected upper-right paper tab from the underlying blouse shoulder contour using a manually drawn quadrilateral.",
            "Exclude the left-side rectangular attachment tab.",
            "Keep all other tiny/ambiguous components unassigned rather than guessing."
        ],
        "limitations": [
            "Run48 is a manually reviewed diagnostic refinement, not SAM segmentation.",
            "Component-to-layer assignments are based on visual inspection of the source candidate and crops.",
            "A few tiny/ambiguous residual pixels remain unassigned.",
            "Drape alpha remains inherited from a flattened white-background PDF-derived silhouette; true textile transmission alpha is not recovered.",
            "The transparent source crop does not contain hidden blouse/longyi pixels under the shawl.",
            "No Thiri v5 alignment or final P01 composite performed."
        ],
        "gate": {
            "major_residual_component_audit": "PASS_DIAGNOSTIC",
            "three_masks_refined": "PASS_DIAGNOSTIC",
            "unassigned_pixels_reduced": "PASS_DIAGNOSTIC",
            "manual_human_approval": "PENDING",
            "true_drape_alpha": "NOT_RECOVERED",
            "thiri_alignment": "NOT_RUN",
            "final_composite": "NOT_RUN",
            "production": "HOLD"
        }
    }
    (outdir / "RUN48_P01_REFINEMENT_METRICS.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--masks", nargs=3, required=True)
    p.add_argument("--output-dir", required=True)
    a = p.parse_args()
    print(json.dumps(run(a.input, a.masks, a.output_dir), indent=2))