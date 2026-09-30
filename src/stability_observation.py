"""Stage 14 deterministic stability observation controller."""

from dataclasses import dataclass


@dataclass(frozen=True)
class StabilityObservation:
    observed: bool
    samples: int
    healthy_samples: int
    stable: bool
    detail: str


class StabilityObservationController:
    """Evaluate bounded telemetry samples without claiming production SLO compliance."""

    def observe(self, samples: list[dict[str, bool]]) -> StabilityObservation:
        if not samples:
            raise ValueError("stability observation requires samples")
        healthy = sum(
            1 for sample in samples
            if sample and all(value is True for value in sample.values())
        )
        stable = healthy == len(samples)
        detail = "all observed signals passed" if stable else "one or more observed signals failed"
        return StabilityObservation(True, len(samples), healthy, stable, detail)
