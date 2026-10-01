"""Stage 15 deterministic optimization evidence comparison."""
from dataclasses import dataclass


@dataclass(frozen=True)
class OptimizationComparison:
    metric: str
    before: float
    after: float
    direction: str
    improved: bool
    delta: float


class OptimizationEvidenceController:
    """Compare explicitly supplied like-for-like measurements without inventing gains."""

    DIRECTIONS = {"higher": "higher", "lower": "lower"}

    def compare(
        self, *, metric: str, before: float, after: float, direction: str
    ) -> OptimizationComparison:
        if not isinstance(metric, str) or not metric.strip():
            raise ValueError("metric is required")
        for name, value in (("before", before), ("after", after)):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name} measurement must be numeric")
        if direction not in self.DIRECTIONS:
            raise ValueError("direction must be 'higher' or 'lower'")
        delta = float(after) - float(before)
        improved = after > before if direction == "higher" else after < before
        return OptimizationComparison(
            metric.strip(), float(before), float(after), direction, improved, delta
        )
