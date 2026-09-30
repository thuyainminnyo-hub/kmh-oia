"""Small local performance baseline for the deterministic KMH OIA text path."""

from __future__ import annotations

import json
import statistics
import time

from src.main import run


def measure(iterations: int = 20) -> dict[str, float | int]:
    durations_ms: list[float] = []
    for index in range(iterations):
        started = time.perf_counter()
        response, _ = run(f"performance baseline {index}", session_id=f"perf-{index}")
        elapsed_ms = (time.perf_counter() - started) * 1000
        if response != f"performance baseline {index}":
            raise AssertionError("runtime response mismatch")
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
