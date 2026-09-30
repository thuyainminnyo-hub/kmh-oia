"""Repeatable Stage 12 performance validation for the deterministic text runtime."""

from __future__ import annotations

import json
import statistics
import time

from src.main import run


ITERATIONS = 50
MEDIAN_TARGET_MS = 100.0
MAX_TARGET_MS = 250.0


def measure(iterations: int = ITERATIONS) -> dict[str, float | int | bool]:
    durations_ms: list[float] = []
    for index in range(iterations):
        started = time.perf_counter()
        response, trace = run(
            f"stage12 performance validation {index}",
            session_id=f"pv4-{index}",
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        if response != f"stage12 performance validation {index}":
            raise AssertionError("runtime response mismatch")
        if not trace.events or trace.events[-1].stage != "trace":
            raise AssertionError("trace did not complete")
        durations_ms.append(elapsed_ms)

    median_ms = statistics.median(durations_ms)
    max_ms = max(durations_ms)
    return {
        "iterations": iterations,
        "min_ms": min(durations_ms),
        "median_ms": median_ms,
        "mean_ms": statistics.mean(durations_ms),
        "max_ms": max_ms,
        "median_target_ms": MEDIAN_TARGET_MS,
        "max_target_ms": MAX_TARGET_MS,
        "acceptance_pass": median_ms <= MEDIAN_TARGET_MS and max_ms <= MAX_TARGET_MS,
    }


if __name__ == "__main__":
    result = measure()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["acceptance_pass"]:
        raise SystemExit(1)
