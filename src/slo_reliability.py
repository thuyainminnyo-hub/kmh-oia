"""Stage 14 deterministic SLO/reliability controller."""
from dataclasses import dataclass

@dataclass(frozen=True)
class ReliabilityObservation:
    samples: int
    healthy_samples: int
    observed_success_rate: float
    reliable: bool

class SloReliabilityController:
    """Report observed reliability without inventing production SLO thresholds."""
    def evaluate(self, samples: list[bool]) -> ReliabilityObservation:
        if not samples:
            raise ValueError("reliability evaluation requires samples")
        if any(not isinstance(value, bool) for value in samples):
            raise ValueError("reliability samples must be boolean")
        healthy=sum(1 for value in samples if value)
        rate=healthy/len(samples)
        return ReliabilityObservation(len(samples), healthy, rate, healthy == len(samples))
