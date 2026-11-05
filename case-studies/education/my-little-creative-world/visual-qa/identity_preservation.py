#!/usr/bin/env python3
"""Verify exact RGB preservation inside a protected character mask."""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image


def evaluate_identity_preservation(original_path, output_path, protected_mask_path):
    original = np.asarray(Image.open(original_path).convert("RGB"), dtype=np.int16)
    output_image = Image.open(output_path).convert("RGBA")
    output = np.asarray(output_image.convert("RGB"), dtype=np.int16)
    mask = np.asarray(Image.open(protected_mask_path).convert("L"), dtype=np.uint8)

    if original.shape != output.shape:
        raise ValueError("Original and output RGB dimensions must match")
    if mask.shape != original.shape[:2]:
        raise ValueError("Protected mask dimensions must match the source image")

    protected = mask > 0
    opaque_core = mask == 255
    if not protected.any() or not opaque_core.any():
        raise ValueError("Protected mask must contain nonzero and fully opaque core pixels")

    delta = np.abs(output - original)
    changed = np.any(delta != 0, axis=2)
    core_count = int(opaque_core.sum())
    core_changed = int((changed & opaque_core).sum())
    protected_count = int(protected.sum())
    protected_changed = int((changed & protected).sum())

    return {
        "image_width": int(original.shape[1]),
        "image_height": int(original.shape[0]),
        "protected_mask_pixels": protected_count,
        "fully_opaque_protected_core_pixels": core_count,
        "exact_rgb_matches_in_opaque_core": core_count - core_changed,
        "changed_rgb_pixels_in_opaque_core": core_changed,
        "opaque_core_exact_match_ratio": round((core_count - core_changed) / core_count, 8),
        "changed_rgb_pixels_in_full_protected_mask": protected_changed,
        "max_channel_delta_in_opaque_core": int(delta[opaque_core].max()) if core_count else 0,
        "pass": bool(core_changed == 0),
        "note": "Exactness applies to RGB values in the fully opaque protected-mask core only; feathered boundary pixels and reconstructed body are excluded."
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--protected-mask", required=True)
    parser.add_argument("--report", default="identity-preservation-report.json")
    args = parser.parse_args()
    result = evaluate_identity_preservation(args.original, args.output, args.protected_mask)
    Path(args.report).write_text(json.dumps(result, indent=2) + "\\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
