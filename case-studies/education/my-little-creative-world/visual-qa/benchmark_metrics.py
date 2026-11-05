#!/usr/bin/env python3
"""Metrics for comparing proposed segmentation masks with human-reviewed masks."""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image


def load_binary(path):
    return np.asarray(Image.open(path).convert("L")) > 0


def boundary(mask):
    mask = np.asarray(mask, dtype=bool)
    padded = np.pad(mask, 1, constant_values=False)
    eroded = (
        padded[1:-1, 1:-1]
        & padded[:-2, 1:-1]
        & padded[2:, 1:-1]
        & padded[1:-1, :-2]
        & padded[1:-1, 2:]
    )
    return mask & ~eroded


def score_masks(prediction, ground_truth, tolerance=1):
    pred = np.asarray(prediction, dtype=bool)
    truth = np.asarray(ground_truth, dtype=bool)
    if pred.shape != truth.shape:
        raise ValueError("Prediction and ground-truth masks must have identical dimensions")

    union = int(np.logical_or(pred, truth).sum())
    intersection = int(np.logical_and(pred, truth).sum())
    iou = intersection / union if union else 1.0

    pred_edge = boundary(pred)
    truth_edge = boundary(truth)
    if tolerance > 0:
        def dilate(mask, radius):
            result = mask.copy()
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx * dx + dy * dy <= radius * radius:
                        shifted = np.roll(np.roll(mask, dy, axis=0), dx, axis=1)
                        if dy < 0: shifted[dy:, :] = False
                        elif dy > 0: shifted[:dy, :] = False
                        if dx < 0: shifted[:, dx:] = False
                        elif dx > 0: shifted[:, :dx] = False
                        result |= shifted
            return result
        pred_near_truth = np.logical_and(pred_edge, dilate(truth_edge, tolerance)).sum()
        truth_near_pred = np.logical_and(truth_edge, dilate(pred_edge, tolerance)).sum()
    else:
        pred_near_truth = np.logical_and(pred_edge, truth_edge).sum()
        truth_near_pred = pred_near_truth
    precision = pred_near_truth / pred_edge.sum() if pred_edge.sum() else (1.0 if not truth_edge.any() else 0.0)
    recall = truth_near_pred / truth_edge.sum() if truth_edge.sum() else (1.0 if not pred_edge.any() else 0.0)
    bf = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"iou": round(float(iou), 6), "boundary_f_score": round(float(bf), 6),
            "prediction_pixels": int(pred.sum()), "ground_truth_pixels": int(truth.sum()),
            "tolerance_px": int(tolerance)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prediction", required=True)
    parser.add_argument("--ground-truth", required=True)
    parser.add_argument("--report", default="segmentation-benchmark.json")
    parser.add_argument("--tolerance", type=int, default=1)
    args = parser.parse_args()
    result = score_masks(load_binary(args.prediction), load_binary(args.ground_truth), args.tolerance)
    Path(args.report).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
