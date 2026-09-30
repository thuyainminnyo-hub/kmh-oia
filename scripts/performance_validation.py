"""Repeatable Stage 12 performance evidence for the deterministic text runtime."""

from __future__ import annotations

import json
import statistics
import time

from src.main import run


ITERATIONS = 50


def measure(iterations: int = ITERATIONS) -> dict[str, float | int]:
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

    return {
        "iterations": iterations,
        "min_ms": min(durations_ms),
        "median_ms": statistics.median(durations_ms),
        "mean_ms": statistics.mean(durations_ms),
        "max_ms": max(durations_ms),
    }


if __name__ == "__main__":
    print(json.dumps(measure(), indent=2, sort_keys=True))
