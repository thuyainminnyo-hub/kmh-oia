"""Stage 14 deterministic operational baseline builder."""
from dataclasses import dataclass

@dataclass(frozen=True)
class OperationalBaseline:
    samples: int
    healthy_samples: int
    success_rate: float
    stable: bool

class OperationalBaselineBuilder:
    """Build a bounded baseline from observed samples; no production SLO is inferred."""
    def build(self, samples: list[dict[str, bool]]) -> OperationalBaseline:
        if not samples:
            raise ValueError("baseline requires samples")
        healthy=sum(1 for sample in samples if sample and all(v is True for v in sample.values()))
        rate=healthy/len(samples)
        return OperationalBaseline(len(samples), healthy, rate, healthy == len(samples))
