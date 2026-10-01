"""Stage 15 deterministic optimization validation and regression guard."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class OptimizationValidation:
    metric: str
    baseline: float
    observed: float
    direction: str
    regression: bool
    validated: bool
    reason: str


class OptimizationRegressionGuard:
    """Validate comparable measurements against an explicit operator-supplied baseline."""

    DIRECTIONS = {"higher", "lower"}

    def evaluate(
        self, *, metric: str, baseline: float, observed: float, direction: str
    ) -> OptimizationValidation:
        if not isinstance(metric, str) or not metric.strip():
            raise ValueError("metric is required")
        for name, value in (("baseline", baseline), ("observed", observed)):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name} measurement must be numeric")
            if not math.isfinite(value):
                raise ValueError(f"{name} measurement must be finite")
        if direction not in self.DIRECTIONS:
            raise ValueError("direction must be 'higher' or 'lower'")
        regression = observed < baseline if direction == "higher" else observed > baseline
        return OptimizationValidation(
            metric.strip(), float(baseline), float(observed), direction,
            regression, True,
            "regression detected" if regression else "no regression detected",
        )

    def require_no_regression(self, result: OptimizationValidation) -> None:
        if not isinstance(result, OptimizationValidation) or not result.validated:
            raise RuntimeError("optimization validation is required")
        if result.regression:
            raise RuntimeError(f"optimization regression detected: {result.metric}")
