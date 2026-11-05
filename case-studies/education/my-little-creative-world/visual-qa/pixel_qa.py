#!/usr/bin/env python3
"""Evidence-first pixel QA for identity-preserving character outfit composites."""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image


def load_rgb(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)


def load_mask(path, shape):
    mask = np.asarray(Image.open(path).convert("L")) > 0
    if mask.shape != shape:
        raise ValueError(f"Mask size {mask.shape} does not match image size {shape}")
    return mask


def evaluate(original_path, output_path, target_mask_path, protected_mask_path, threshold=0):
    original = load_rgb(original_path)
    output = load_rgb(output_path)
    if original.shape != output.shape:
        raise ValueError("Original and output image dimensions must match")
    target = load_mask(target_mask_path, original.shape[:2])
    protected = load_mask(protected_mask_path, original.shape[:2])
    changed = np.any(np.abs(output - original) > threshold, axis=2)

    target_count = int(target.sum())
    changed_target = int((changed & target).sum())
    protected_count = int(protected.sum())
    protected_changed = int((changed & protected).sum())
    spillover = int((changed & ~target & ~protected).sum())
    uncovered = int((target & ~changed).sum())

    return {
        "image_width": int(original.shape[1]),
        "image_height": int(original.shape[0]),
        "target_pixels": target_count,
        "changed_target_pixels": changed_target,
        "uncovered_target_pixels": uncovered,
        "target_coverage_ratio": round(changed_target / target_count, 6) if target_count else None,
        "protected_pixels": protected_count,
        "protected_changed_pixels": protected_changed,
        "protected_preservation_ratio": round(1 - protected_changed / protected_count, 6) if protected_count else None,
        "spillover_pixels_outside_target_and_protected": spillover,
        "pass": bool(target_count > 0 and protected_count > 0 and uncovered == 0 and protected_changed == 0 and spillover == 0)
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--target-mask", required=True)
    parser.add_argument("--protected-mask", required=True)
    parser.add_argument("--report", default="pixel-qa-report.json")
    parser.add_argument("--threshold", type=int, default=0)
    args = parser.parse_args()
    result = evaluate(args.original, args.output, args.target_mask, args.protected_mask, args.threshold)
    Path(args.report).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
