"""Evaluate whether a governed decision produced the intended outcome."""

from dataclasses import dataclass
from typing import Literal

from .decision_queue import DecisionItem
from .live_runtime_bridge import ExecutionRecord


DecisionQuality = Literal["GOOD", "NEUTRAL", "POOR"]


@dataclass(frozen=True)
class DecisionOutcome:
    decision_id: str
    command_id: str
    outcome_positive: bool
    quality: DecisionQuality
    reason: str


class DecisionOutcomeEvaluator:
    """Close the decision loop from execution outcome back to decision quality."""

    def evaluate(
        self,
        decision: DecisionItem,
        execution: ExecutionRecord,
        *,
        outcome_positive: bool,
    ) -> DecisionOutcome:
        if decision.status != "APPROVED":
            raise ValueError("only approved decisions can be evaluated")
        if execution.command_id != self._command_id(execution):
            raise ValueError("execution command identity is invalid")
        if execution.final_status != "LEARNED":
            raise ValueError("decision outcome requires learned execution")
        quality: DecisionQuality = "GOOD" if outcome_positive else "POOR"
        reason = (
            "Approved decision produced a positive verified outcome."
            if outcome_positive
            else "Approved decision produced a negative verified outcome."
        )
        return DecisionOutcome(decision.id, execution.command_id, outcome_positive, quality, reason)

    def _command_id(self, execution: ExecutionRecord) -> str:
        if not execution.command_id.strip():
            raise ValueError("execution command_id is required")
        return execution.command_id
