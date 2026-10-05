"""Select the next governed action for the Command Center."""

from dataclasses import dataclass
from typing import Literal

from .command_center_cycle_adapter import CommandCenterView


ActionKind = Literal["BLOCKER", "QA", "EVIDENCE", "DECISION", "SIGNAL", "OBJECTIVE", "NONE"]


@dataclass(frozen=True)
class NextAction:
    kind: ActionKind
    priority: int
    action: str
    reason: str


class NextActionEngine:
    """Deterministically rank operational pressure without executing anything."""

    def recommend(self, view: CommandCenterView) -> NextAction:
        if view.blockers:
            return NextAction("BLOCKER", 1, f"Resolve blocker: {view.blockers[0]}", "Blocked execution has the highest operational priority.")
        if view.qa_pending:
            return NextAction("QA", 2, "Verify completed work with evidence.", "Completed work is waiting for QA.")
        if view.evidence_pending:
            return NextAction("EVIDENCE", 3, "Attach evidence to completed work.", "Verification cannot proceed without evidence.")
        if view.pending_decisions:
            return NextAction("DECISION", 4, f"Review pending decision: {view.decision_ids[0]}", "Governance backlog is waiting for a decision.")
        if view.signals:
            return NextAction("SIGNAL", 5, "Review active intelligence signals.", "Signals require interpretation before action.")
        if view.primary_objective:
            return NextAction("OBJECTIVE", 6, view.primary_objective, "No higher-priority operational pressure is present.")
        return NextAction("NONE", 99, "No immediate action.", "No blocker, QA, evidence, decision, signal, or objective is pending.")
