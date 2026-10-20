"""Validate the JSON contract of the KMH OIA performance evidence artifact."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any


REQUIRED_METRICS = ("min_ms", "median_ms", "mean_ms", "max_ms")


def validate_performance_payload(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["top-level performance report must be a JSON object"]

    iterations = payload.get("iterations")
    if isinstance(iterations, bool) or not isinstance(iterations, int) or iterations < 1:
        errors.append("iterations must be an integer greater than zero")

    metrics: dict[str, float] = {}
    for key in REQUIRED_METRICS:
        value = payload.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"{key} must be a number")
            continue
        numeric = float(value)
        if not math.isfinite(numeric) or numeric < 0:
            errors.append(f"{key} must be finite and non-negative")
            continue
        metrics[key] = numeric

    if len(metrics) == len(REQUIRED_METRICS):
        if metrics["min_ms"] > metrics["median_ms"]:
            errors.append("min_ms must be less than or equal to median_ms")
        if metrics["median_ms"] > metrics["max_ms"]:
            errors.append("median_ms must be less than or equal to max_ms")
        if not metrics["min_ms"] <= metrics["mean_ms"] <= metrics["max_ms"]:
            errors.append("mean_ms must be between min_ms and max_ms")
    return errors


def validate_performance_file(path: Path | str) -> list[str]:
    file_path = Path(path)
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [f"performance report not found: {file_path}"]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"performance report is unreadable or invalid JSON ({type(exc).__name__})"]
    return validate_performance_payload(payload)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("usage: python scripts/validate_performance_artifact.py PATH")
        return 2
    errors = validate_performance_file(args[0])
    if errors:
        for error in errors:
            print(f"performance artifact validation: {error}")
        return 1
    print("performance artifact validation: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
