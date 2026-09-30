"""Bounded concurrent load evidence for the deterministic KMH OIA runtime."""

from __future__ import annotations

import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor

from src.main import run


ITERATIONS = 20
WORKERS = 4


def measure(iterations: int = ITERATIONS, workers: int = WORKERS) -> dict[str, float | int]:
    if iterations < 1:
        raise ValueError("iterations must be positive")
    if workers < 1:
        raise ValueError("workers must be positive")

    started = time.perf_counter()

    def execute(index: int) -> float:
        call_started = time.perf_counter()
        response, trace = run(
            f"stage13 load validation {index}",
            session_id=f"stage13-load-{index}",
        )
        if response != f"stage13 load validation {index}":
            raise AssertionError("runtime response mismatch")
        if not trace.events or trace.events[-1].stage != "trace":
            raise AssertionError("trace did not complete")
        return (time.perf_counter() - call_started) * 1000

    with ThreadPoolExecutor(max_workers=workers) as pool:
        durations_ms = list(pool.map(execute, range(iterations)))

    wall_ms = (time.perf_counter() - started) * 1000
    return {
        "iterations": iterations,
        "workers": workers,
        "wall_ms": wall_ms,
        "min_ms": min(durations_ms),
        "median_ms": statistics.median(durations_ms),
        "mean_ms": statistics.mean(durations_ms),
        "max_ms": max(durations_ms),
        "completed": len(durations_ms),
    }


if __name__ == "__main__":
    print(json.dumps(measure(), indent=2, sort_keys=True))
