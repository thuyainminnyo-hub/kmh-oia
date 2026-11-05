#!/usr/bin/env python3
"""Deterministic taper for the lower neck edge of the protected original-head mask."""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image


def smoothstep(value):
    value = np.clip(value, 0.0, 1.0)
    return value * value * (3.0 - 2.0 * value)


def refine_neck_mask(mask, y_start=378.0, y_end=412.0,
                     x_left_outer=398.0, x_left_inner=420.0,
                     x_right_inner=598.0, x_right_outer=620.0):
    """Return uint8 mask; reduce only the lower-centre neck opacity.

    Side regions (where ear/earring strands may hang) remain protected.
    The fade uses smoothstep horizontally and linear vertical taper.
    """
    source = np.asarray(mask)
    if source.ndim != 2:
        raise ValueError("Protected mask must be a 2D grayscale image")
    if y_end <= y_start or x_left_inner <= x_left_outer or x_right_outer <= x_right_inner:
        raise ValueError("Taper coordinates must be strictly increasing")
    if x_right_inner <= x_left_inner:
        raise ValueError("Inner horizontal bounds must be ordered")

    h, w = source.shape
    yy, xx = np.mgrid[0:h, 0:w]
    vertical_keep = np.clip((y_end - yy) / (y_end - y_start), 0.0, 1.0)
    left_gate = smoothstep((xx - x_left_outer) / (x_left_inner - x_left_outer))
    right_gate = smoothstep((x_right_outer - xx) / (x_right_outer - x_right_inner))
    central_gate = left_gate * right_gate
    factor = 1.0 - (1.0 - vertical_keep) * central_gate
    refined = np.rint(source.astype(np.float32) * factor).clip(0, 255).astype(np.uint8)
    return refined


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mask", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", default="neck-mask-refinement.json")
    args = parser.parse_args()
    source = np.asarray(Image.open(args.mask).convert("L"), dtype=np.uint8)
    refined = refine_neck_mask(source)
    Image.fromarray(refined, mode="L").save(args.output)
    report = {
        "input_shape": list(source.shape),
        "output_shape": list(refined.shape),
        "input_nonzero": int((source > 0).sum()),
        "output_nonzero": int((refined > 0).sum()),
        "output_opaque_core": int((refined == 255).sum()),
        "parameters": {
            "y_start": 378, "y_end": 412,
            "x_left_outer": 398, "x_left_inner": 420,
            "x_right_inner": 598, "x_right_outer": 620
        }
    }
    Path(args.report).write_text(json.dumps(report, indent=2) + "\\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
