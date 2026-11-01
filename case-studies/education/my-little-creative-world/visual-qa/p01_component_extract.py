#!/usr/bin/env python3
"""Extract the largest non-transparent connected component from a P01 RGBA panel.

This produces a diagnostic cutout only. It does not repair cropped edges or
remove attached tabs within the main connected component.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image


def extract_largest_component(image_path, output_path, mask_path, report_path):
    rgba = np.asarray(Image.open(image_path).convert("RGBA"), dtype=np.uint8)
    alpha = rgba[:, :, 3]
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("Install opencv-python-headless to use this utility") from exc

    count, labels, stats, _ = cv2.connectedComponentsWithStats((alpha > 0).astype(np.uint8), 8)
    if count <= 1:
        raise ValueError("No non-transparent component found")
    component_index = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x = int(stats[component_index, cv2.CC_STAT_LEFT])
    y = int(stats[component_index, cv2.CC_STAT_TOP])
    w = int(stats[component_index, cv2.CC_STAT_WIDTH])
    h = int(stats[component_index, cv2.CC_STAT_HEIGHT])
    area = int(stats[component_index, cv2.CC_STAT_AREA])
    mask = (labels == component_index).astype(np.uint8) * 255

    output = rgba.copy()
    output[:, :, 3] = ((alpha.astype(np.uint16) * mask.astype(np.uint16)) // 255).astype(np.uint8)
    Image.fromarray(output[y:y+h, x:x+w], "RGBA").save(output_path)
    Image.fromarray(mask[y:y+h, x:x+w], "L").save(mask_path)

    report = {
        "source_size": [int(rgba.shape[1]), int(rgba.shape[0])],
        "connected_component_count": int(count - 1),
        "largest_component": {
            "bbox_xywh": [x, y, w, h],
            "pixels": area,
            "touches_left": x == 0,
            "touches_top": y == 0,
            "touches_right": x + w == rgba.shape[1],
            "touches_bottom": y + h == rgba.shape[0]
        },
        "warning": "Diagnostic only: attached tabs may remain; edge-touch may indicate missing/cropped garment pixels."
    }
    Path(report_path).write_text(json.dumps(report, indent=2) + "\\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--mask", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    print(json.dumps(extract_largest_component(args.input, args.output, args.mask, args.report), indent=2))
