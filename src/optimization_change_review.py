"""Stage 15 optimization change evidence and review gate."""
from dataclasses import dataclass

from src.optimization_regression import OptimizationValidation


@dataclass(frozen=True)
class OptimizationReview:
    change_id: str
    metric: str
    reviewer: str
    phase: str
    accepted: bool
    reason: str = ""


class OptimizationChangeReviewGate:
    """Require explicit change identity, validated comparison, and human review."""

    def prepare(
        self, *, change_id: str, comparison: OptimizationValidation
    ) -> OptimizationReview:
        if not isinstance(change_id, str) or not change_id.strip():
            raise ValueError("change_id is required")
        if not isinstance(comparison, OptimizationValidation) or not comparison.validated:
            raise ValueError("validated optimization comparison is required")
        if comparison.regression:
            return OptimizationReview(
                change_id.strip(), comparison.metric, "", "blocked", False,
                "regression evidence blocks acceptance",
            )
        return OptimizationReview(
            change_id.strip(), comparison.metric, "", "review_pending", False,
            "awaiting explicit reviewer decision",
        )

    def review(
        self, state: OptimizationReview, *, reviewer: str, accepted: bool
    ) -> OptimizationReview:
        if state.phase != "review_pending":
            raise RuntimeError("review requires a pending, non-regressed change")
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise ValueError("reviewer is required")
        if not isinstance(accepted, bool):
            raise ValueError("accepted must be boolean")
        return OptimizationReview(
            state.change_id, state.metric, reviewer.strip(),
            "accepted" if accepted else "rejected", accepted,
            "explicit review accepted" if accepted else "explicit review rejected",
        )

    def require_accepted(self, state: OptimizationReview) -> None:
        if not isinstance(state, OptimizationReview) or state.phase != "accepted" or not state.accepted or not state.reviewer:
            raise RuntimeError("optimization change has not been accepted by review")
